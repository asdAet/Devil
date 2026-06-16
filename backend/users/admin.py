"""Django Admin для custom user model."""

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.html import format_html, mark_safe
from django.views.decorators.http import require_POST

from .models import Profile, User, UserTwoFactor


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("login", "email")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        if not password2:
            return password2
        validate_password(password2, user=self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Password")
    new_password = forms.CharField(
        label="Новый пароль", widget=forms.PasswordInput,
        required=False, help_text="Оставьте пустым чтобы не менять.",
    )
    new_password_confirm = forms.CharField(
        label="Подтвердите новый пароль", widget=forms.PasswordInput, required=False,
    )

    class Meta:
        model = User
        fields = (
            "login", "email", "email_verified", "password",
            "new_password", "new_password_confirm",
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
        )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("new_password")
        pw2 = cleaned.get("new_password_confirm")
        if pw and pw != pw2:
            self.add_error("new_password_confirm", "Пароли не совпадают")
        if pw:
            validate_password(pw, user=self.instance)
        return cleaned


class ProfileInlineForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("name", "image", "bio")


class ProfileInline(admin.StackedInline):
    model = Profile
    form = ProfileInlineForm
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ("name", "image", "bio", "last_seen", "avatar_preview")
    readonly_fields = ("last_seen", "avatar_preview")
    extra = 0

    @admin.display(description="Avatar")
    def avatar_preview(self, obj):
        if obj and getattr(obj, "image", None):
            try:
                return format_html(
                    '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:50%;">',
                    obj.image.url,
                )
            except ValueError:
                pass
        return "-"


def _twofa_html(user: User) -> dict[str, str]:
    cred = UserTwoFactor.objects.filter(user=user).first()
    enabled = bool(cred and cred.is_enabled)

    if enabled:
        assert cred is not None
        dt = cred.enabled_at.strftime("%d.%m.%Y %H:%M") if cred.enabled_at else ""
        status = (
            '<span style="color:#28a745;font-weight:bold;">✓ Включена</span>'
            + (f' <span style="color:#6c757d;font-size:12px;">(с {dt})</span>' if dt else "")
        )

        from users.application.two_factor_service import _decrypt_secret, _qr_svg_data_uri
        try:
            assert cred.secret_encrypted
            secret = _decrypt_secret(cred.secret_encrypted)
            import pyotp
            uri = pyotp.TOTP(secret, interval=30).provisioning_uri(
                name=str(user.login or user.pk), issuer_name="Devil",
            )
            qr = _qr_svg_data_uri(uri)
            qr_html = (
                '<div class="twofa-data">'
                f'<img src="{qr}" class="twofa-qr" alt="QR">'
                '<div class="twofa-key">'
                '<span class="twofa-key-label">Ключ:</span>'
                f'<code>{secret}</code>'
                '</div></div>'
            )
        except Exception:
            qr_html = "Ошибка расшифровки ключа"

        actions = (
            '<button type="button" class="default twofa-toggle" '
            'data-action="disable" style="color:#dc3545;" '
            "onclick=\"return confirm('Отключить 2FA?')\">"
            "Отключить 2FA</button>"
        )
    else:
        status = '<span style="color:#dc3545;">✗ Отключена</span>'
        qr_html = "—"
        actions = (
            '<button type="button" class="default twofa-toggle" '
            'data-action="enable">Включить 2FA</button>'
        )

    return {"status": status, "qr": qr_html, "actions": actions}


@require_POST
def twofa_toggle_view(request: HttpRequest, user_id: int) -> JsonResponse:
    if not request.user.is_superuser:
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    action = request.POST.get("action")

    if action == "enable":
        credential, _ = UserTwoFactor.objects.get_or_create(user=user)
        if credential.is_enabled:
            return JsonResponse({"error": "2FA already enabled"}, status=400)

        from users.application.two_factor_service import (
            _decrypt_secret,
            _encrypt_secret,
            _qr_svg_data_uri,
        )
        import pyotp

        secret = _decrypt_secret(credential.secret_encrypted) if credential.secret_encrypted else None
        if not secret:
            secret = pyotp.random_base32()
            credential.secret_encrypted = _encrypt_secret(secret)

        credential.enabled_at = timezone.now()
        credential.save(update_fields=["secret_encrypted", "enabled_at", "updated_at"])

    elif action == "disable":
        credential = UserTwoFactor.objects.filter(user=user).first()
        if not credential or not credential.is_enabled:
            return JsonResponse({"error": "2FA already disabled"}, status=400)

        credential.secret_encrypted = ""
        credential.enabled_at = None
        credential.last_accepted_timestep = None
        credential.save(update_fields=[
            "secret_encrypted", "enabled_at",
            "last_accepted_timestep", "updated_at",
        ])
    else:
        return JsonResponse({"error": "Invalid action"}, status=400)

    html = _twofa_html(user)
    return JsonResponse({"ok": True, **html})


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [ProfileInline]

    list_display = (
        "login", "email", "email_verified", "is_staff", "is_active",
        "two_factor_status", "profile_last_seen", "date_joined",
    )
    list_select_related = ("profile",)
    search_fields = ("login", "email", "profile__name", "public_id")
    list_filter = ("is_staff", "is_active", "is_superuser", "email_verified", "date_joined")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")
    list_per_page = 25
    actions = ("reset_password_action", "enable_2fa_action", "disable_2fa_action")

    fieldsets = (
        (None, {"fields": ("login", "password")}),
        ("Identity", {"fields": ("email", "email_verified", "public_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
        ("Смена пароля", {"fields": ("new_password", "new_password_confirm")}),
        ("Двухфакторная аутентификация", {"fields": ("twofa_status", "twofa_qr", "twofa_actions")}),
    )
    readonly_fields = (
        "public_id", "last_login", "date_joined",
        "twofa_status", "twofa_qr", "twofa_actions",
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("login", "email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    class Media:
        css = {"all": ("admin/css/two_factor_admin.css",)}
        js = ("admin/js/two_factor_admin.js",)

    def get_urls(self):
        from django.urls import path
        custom = [
            path("<int:user_id>/twofa-toggle/", self.admin_site.admin_view(twofa_toggle_view), name="users_user_twofa_toggle"),
        ]
        return custom + super().get_urls()

    def has_delete_permission(self, request: HttpRequest, obj=None):
        if obj and obj.pk == request.user.pk:
            return False
        return request.user.is_superuser

    def save_model(self, request: HttpRequest, obj, form, change):
        new_password = form.cleaned_data.get("new_password")
        if new_password:
            obj.set_password(new_password)
            self.message_user(request, f"Пароль для {obj.login} изменён.")
        super().save_model(request, obj, form, change)

    def twofa_status(self, obj):
        return mark_safe('<div id="twofa_status">{}</div>'.format(_twofa_html(obj)["status"]))

    def twofa_qr(self, obj):
        return mark_safe('<div id="twofa_qr">{}</div>'.format(_twofa_html(obj)["qr"]))

    def twofa_actions(self, obj):
        return mark_safe('<div id="twofa_actions">{}</div>'.format(_twofa_html(obj)["actions"]))

    @admin.display(description="2FA")
    def two_factor_status(self, obj):
        cred = UserTwoFactor.objects.filter(user=obj).first()
        if cred and cred.is_enabled:
            return format_html('<span style="color:green;font-weight:bold;">ON</span>')
        return format_html('<span style="color:gray;">OFF</span>')

    # -- Bulk actions --

    @admin.action(description="Сбросить пароль")
    def reset_password_action(self, request: HttpRequest, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите одного пользователя.", messages.WARNING)
            return
        user = queryset.first()

        from django.template.response import TemplateResponse
        if request.method == "POST" and "_confirm_reset" in request.POST:
            pw = request.POST.get("new_password", "")
            pw2 = request.POST.get("new_password_confirm", "")
            if not pw:
                self.message_user(request, "Введите пароль.", messages.ERROR)
            elif pw != pw2:
                self.message_user(request, "Пароли не совпадают.", messages.ERROR)
            else:
                user.set_password(pw)
                user.save(update_fields=["password"])
                self.message_user(request, f"Пароль для {user.login} сброшен.")
                return None

        return TemplateResponse(
            request, "admin/reset_password.html",
            {"user": user, "title": f"Сброс пароля: {user.login}"},
        )

    @admin.action(description="Включить 2FA")
    def enable_2fa_action(self, request: HttpRequest, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите одного пользователя.", messages.WARNING)
            return
        user = queryset.first()

        cred = UserTwoFactor.objects.filter(user=user).first()
        if cred and cred.is_enabled:
            self.message_user(request, f"2FA уже включена для {user.login}.", messages.WARNING)
            return

        from users.application.two_factor_service import begin_totp_setup, confirm_totp_setup
        setup = begin_totp_setup(user)

        from django.template.response import TemplateResponse
        if request.method == "POST" and "_confirm_2fa" in request.POST:
            code = request.POST.get("code", "").strip()
            if len(code) != 6 or not code.isdigit():
                self.message_user(request, "Код должен содержать ровно 6 цифр.", messages.ERROR)
            else:
                try:
                    confirm_totp_setup(user, code)
                    self.message_user(request, f"2FA включена для {user.login}.")
                    return None
                except Exception as exc:
                    self.message_user(request, f"Ошибка: {exc}", messages.ERROR)

        return TemplateResponse(
            request, "admin/enable_2fa.html",
            {"user": user, "setup": setup, "title": f"Включение 2FA: {user.login}"},
        )

    @admin.action(description="Отключить 2FA")
    def disable_2fa_action(self, request: HttpRequest, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите одного пользователя.", messages.WARNING)
            return
        user = queryset.first()

        cred = UserTwoFactor.objects.filter(user=user).first()
        if not cred or not cred.is_enabled:
            self.message_user(request, f"2FA не включена для {user.login}.", messages.WARNING)
            return

        from django.template.response import TemplateResponse
        if request.method == "POST" and "_confirm_disable" in request.POST:
            cred.secret_encrypted = ""
            cred.enabled_at = None
            cred.last_accepted_timestep = None
            cred.save(update_fields=[
                "secret_encrypted", "enabled_at",
                "last_accepted_timestep", "updated_at",
            ])
            self.message_user(request, f"2FA отключена для {user.login}.")
            return None

        return TemplateResponse(
            request, "admin/disable_2fa.html",
            {"user": user, "title": f"Отключение 2FA: {user.login}"},
        )

    @admin.display(description="Last seen", ordering="profile__last_seen")
    def profile_last_seen(self, obj):
        profile = getattr(obj, "profile", None)
        return getattr(profile, "last_seen", None) or "-"
