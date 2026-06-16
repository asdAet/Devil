from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "room_link", "short_message", "date_added", "edited_at")
    list_filter = ("room", "date_added", "edited_at")
    search_fields = ("id", "username", "user__login", "user__email", "message_content", "room__name", "room__public_id")
    date_hierarchy = "date_added"
    readonly_fields = ("user", "room", "date_added", "edited_at", "original_content", "profile_pic")
    list_per_page = 50
    list_select_related = ("room", "user")

    fieldsets = (
        (None, {"fields": ("user", "room", "message_content")}),
        ("Metadata", {"fields": ("username", "profile_pic", "date_added", "edited_at", "original_content")}),
    )

    @admin.display(description="Комната")
    def room_link(self, obj):
        if obj.room_id:
            return format_html(
                '<a href="{}?room__id__exact={}">{}</a>',
                reverse("admin:messages_message_changelist"),
                obj.room_id,
                obj.room,
            )
        return "-"

    @admin.display(description="Сообщение")
    def short_message(self, obj):
        if obj.message_content:
            return (obj.message_content[:80] + "...") if len(obj.message_content) > 80 else obj.message_content
        return ""

    def has_add_permission(self, request):
        return False
