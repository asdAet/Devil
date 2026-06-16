from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from groups.infrastructure.models import InviteLink, JoinRequest, PinnedMessage
from roles.models import Membership, PermissionOverride, Role
from rooms.models import Group, Room


class RoleInline(admin.TabularInline):
    model = Role
    extra = 0
    show_change_link = True
    fields = ("name", "position", "color", "permissions", "is_default")
    ordering = ("-position",)


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    show_change_link = True
    fields = ("user", "nickname", "roles", "is_banned", "muted_until", "joined_at")
    readonly_fields = ("joined_at",)
    raw_id_fields = ("user", "banned_by", "muted_by")
    filter_horizontal = ("roles",)
    autocomplete_fields = ("user",)
    ordering = ("-joined_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").prefetch_related("roles")


class PermissionOverrideInline(admin.TabularInline):
    model = PermissionOverride
    extra = 0
    show_change_link = True
    fields = ("target_role", "target_user", "allow", "deny")
    raw_id_fields = ("target_role", "target_user")


class InviteLinkInline(admin.TabularInline):
    model = InviteLink
    extra = 0
    show_change_link = True
    fields = ("code", "name", "created_by", "expires_at", "max_uses", "use_count", "is_revoked")
    readonly_fields = ("use_count",)
    raw_id_fields = ("created_by",)
    ordering = ("-created_at",)


class JoinRequestInline(admin.TabularInline):
    model = JoinRequest
    extra = 0
    show_change_link = True
    fields = ("user", "status", "invite_link", "message", "reviewed_by", "created_at", "reviewed_at")
    readonly_fields = ("created_at", "reviewed_at")
    raw_id_fields = ("user", "invite_link", "reviewed_by")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "invite_link", "reviewed_by")


class PinnedMessageInline(admin.TabularInline):
    model = PinnedMessage
    extra = 0
    show_change_link = True
    fields = ("message", "pinned_by", "pinned_at")
    readonly_fields = ("pinned_at",)
    raw_id_fields = ("message", "pinned_by")
    ordering = ("-pinned_at",)


def _permission_flags(mask: int) -> str:
    from roles.permissions import Perm
    names = [
        perm.name
        for perm in Perm
        if perm and perm.name and (int(mask) & int(perm))
    ]
    return ", ".join(names) if names else "-"


def _messages_link(obj):
    if obj.pk:
        url = reverse("admin:chat_messages_message_changelist") + "?room__id__exact=%d" % obj.pk
        count = obj.messages.count()
        return format_html(
            '<a href="{}">Посмотреть сообщения ({})</a>',
            url, count,
        )
    return "-"


_messages_link.short_description = "Сообщения"


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "member_count", "is_public",
        "slow_mode_seconds", "join_approval_required", "created_by",
    )
    search_fields = ("id", "name", "public_id", "created_by__login", "description")
    list_filter = ("is_public", "join_approval_required")
    readonly_fields = ("member_count", "created_by", "messages_link")
    list_per_page = 50

    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "description", "public_id", "is_public"),
        }),
        ("Настройки", {
            "fields": ("slow_mode_seconds", "join_approval_required", "max_members"),
        }),
        ("Аватар", {
            "fields": ("avatar", "avatar_crop_x", "avatar_crop_y", "avatar_crop_width", "avatar_crop_height"),
            "classes": ("collapse",),
        }),
        ("Статистика", {
            "fields": ("member_count", "created_by", "messages_link"),
            "classes": ("collapse",),
        }),
    )

    inlines = (
        RoleInline,
        MembershipInline,
        PermissionOverrideInline,
        InviteLinkInline,
        JoinRequestInline,
        PinnedMessageInline,
    )

    actions = ("recalc_member_count",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(kind=Room.Kind.GROUP).select_related("created_by")

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is None:
            readonly.append("kind")
        return readonly

    def save_model(self, request, obj, form, change):
        if not change:
            obj.kind = Room.Kind.GROUP
        super().save_model(request, obj, form, change)

    @admin.display(description="Участники")
    def member_count_display(self, obj):
        return obj.member_count

    @admin.display(description="Сообщения")
    def messages_link(self, obj):
        return _messages_link(obj)

    @admin.action(description="Пересчитать количество участников")
    def recalc_member_count(self, request, queryset):
        updated = 0
        for room in queryset:
            count = room.memberships.filter(is_banned=False).count()
            room.member_count = count
            room.save(update_fields=["member_count"])
            updated += 1
        self.message_user(request, f"Пересчитано для {updated} групп.")


class DirectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "direct_pair_key", "created_by")
    search_fields = ("id", "name", "direct_pair_key", "created_by__login")
    list_filter = ("kind",)
    readonly_fields = ("direct_pair_key", "created_by", "messages_link")
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("name", "kind", "direct_pair_key")}),
        ("Пользователи", {"fields": ("created_by",)}),
        ("Сообщения", {"fields": ("messages_link",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(kind=Room.Kind.GROUP).select_related("created_by")

    @admin.display(description="Сообщения")
    def messages_link(self, obj):
        return _messages_link(obj)


admin.site.register(Room, DirectAdmin)
