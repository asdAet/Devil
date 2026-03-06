from django.contrib import admin

from .models import Friendship


def _friend_from_user_id(obj: Friendship) -> int | None:
    from_user_id = getattr(obj, "from_user_id", None)
    if from_user_id is not None:
        return int(from_user_id)
    from_user_pk = getattr(getattr(obj, "from_user", None), "pk", None)
    return int(from_user_pk) if from_user_pk is not None else None


def _friend_to_user_id(obj: Friendship) -> int | None:
    to_user_id = getattr(obj, "to_user_id", None)
    if to_user_id is not None:
        return int(to_user_id)
    to_user_pk = getattr(getattr(obj, "to_user", None), "pk", None)
    return int(to_user_pk) if to_user_pk is not None else None


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "from_user",
        "from_user_id_value",
        "to_user",
        "to_user_id_value",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("id", "from_user__username", "to_user__username")
    raw_id_fields = ("from_user", "to_user")
    list_select_related = ("from_user", "to_user")
    readonly_fields = ("created_at", "updated_at")
    fields = ("from_user", "to_user", "status", "created_at", "updated_at")
    actions = ("mark_pending", "mark_accepted", "mark_declined", "mark_blocked", "make_mutual_accepted")

    @admin.display(description="From user id")
    def from_user_id_value(self, obj: Friendship) -> int | None:
        return _friend_from_user_id(obj)

    @admin.display(description="To user id")
    def to_user_id_value(self, obj: Friendship) -> int | None:
        return _friend_to_user_id(obj)

    def _set_status(self, queryset, status: str) -> int:
        updated = 0
        for friendship in queryset:
            if friendship.status == status:
                continue
            friendship.status = status
            friendship.save(update_fields=["status", "updated_at"])
            updated += 1
        return updated

    @admin.action(description="Set status: pending")
    def mark_pending(self, request, queryset):
        updated = self._set_status(queryset, Friendship.Status.PENDING)
        self.message_user(request, f"Updated {updated} friendship(s) to pending.")

    @admin.action(description="Set status: accepted")
    def mark_accepted(self, request, queryset):
        updated = self._set_status(queryset, Friendship.Status.ACCEPTED)
        self.message_user(request, f"Updated {updated} friendship(s) to accepted.")

    @admin.action(description="Set status: declined")
    def mark_declined(self, request, queryset):
        updated = self._set_status(queryset, Friendship.Status.DECLINED)
        self.message_user(request, f"Updated {updated} friendship(s) to declined.")

    @admin.action(description="Set status: blocked")
    def mark_blocked(self, request, queryset):
        updated = self._set_status(queryset, Friendship.Status.BLOCKED)
        self.message_user(request, f"Updated {updated} friendship(s) to blocked.")

    @admin.action(description="Make accepted + create reverse accepted rows")
    def make_mutual_accepted(self, request, queryset):
        created_or_updated = 0
        for friendship in queryset.select_related("from_user", "to_user"):
            if friendship.status != Friendship.Status.ACCEPTED:
                friendship.status = Friendship.Status.ACCEPTED
                friendship.save(update_fields=["status", "updated_at"])
            Friendship.objects.update_or_create(
                from_user=friendship.to_user,
                to_user=friendship.from_user,
                defaults={"status": Friendship.Status.ACCEPTED},
            )
            created_or_updated += 1
        self.message_user(request, f"Processed {created_or_updated} friendship pair(s).")
