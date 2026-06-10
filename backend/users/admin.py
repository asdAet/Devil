"""Django Admin для custom user model и профилей."""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.utils.html import format_html

from .models import Profile, User


class UserCreationForm(forms.ModelForm):
    """Форма создания пользователя в Django Admin."""

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
    """Форма редактирования пользователя в Django Admin."""

    password = ReadOnlyPasswordHashField(label="Password")

    class Meta:
        model = User
        fields = (
            "login",
            "email",
            "email_verified",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )


class ProfileInlineForm(forms.ModelForm):
    """Форма профиля внутри карточки пользователя."""

    class Meta:
        model = Profile
        fields = ("name", "image", "bio")


class ProfileInline(admin.StackedInline):
    """Inline профиля в карточке пользователя."""

    model = Profile
    form = ProfileInlineForm
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        "name",
        "image",
        "bio",
        "last_seen",
        "avatar_preview",
    )
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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin для custom User без username."""

    form = UserChangeForm
    add_form = UserCreationForm
    inlines = [ProfileInline]
    list_display = (
        "login",
        "email",
        "email_verified",
        "is_staff",
        "is_active",
        "profile_last_seen",
        "date_joined",
    )
    list_select_related = ("profile",)
    search_fields = ("login", "email", "profile__name", "public_id")
    list_filter = ("is_staff", "is_active", "is_superuser", "email_verified", "date_joined")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("login", "password")}),
        ("Identity", {"fields": ("email", "email_verified", "public_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("public_id", "last_login", "date_joined")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("login", "email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )

    @admin.display(description="Last seen", ordering="profile__last_seen")
    def profile_last_seen(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.last_seen if profile else "-"


class ProfileAdminForm(ProfileInlineForm):
    class Meta(ProfileInlineForm.Meta):
        model = Profile
        fields = ("user", "name", "image", "bio")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Отдельная админка профилей."""

    form = ProfileAdminForm
    list_display = ("user", "user_login", "name", "is_staff", "last_seen", "avatar_preview")
    list_select_related = ("user",)
    list_filter = ("user__is_staff",)
    search_fields = ("user__login", "user__email", "name")
    readonly_fields = ("last_seen", "avatar_preview")
    fields = ("user", "name", "is_staff", "image", "bio", "last_seen", "avatar_preview")

    @admin.display(description="Login", ordering="user__login")
    def user_login(self, obj):
        return getattr(obj.user, "login", "-")

    @admin.display(boolean=True, description="Модератор/админ", ordering="user__is_staff")
    def is_staff(self, obj):
        return getattr(obj.user, "is_staff", False)

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
