"""Delete all users except superusers, handling FK constraints correctly."""

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import User


class Command(BaseCommand):
    help = "Deletes all non-superuser accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        superusers = User.objects.filter(is_superuser=True)
        non_superusers = User.objects.exclude(is_superuser=True)

        self.stdout.write(f"Superusers: {superusers.count()}")
        for u in superusers:
            self.stdout.write(f"  {u.login}")

        self.stdout.write(f"Non-superusers to delete: {non_superusers.count()}")
        for u in non_superusers:
            self.stdout.write(f"  {u.login}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no changes made."))
            return

        from django.contrib.admin.models import LogEntry
        from django.contrib.sessions.models import Session

        from auditlog.infrastructure.models import AuditEvent
        from friends.models import Friendship
        from groups.infrastructure.models import InviteLink, JoinRequest, PinnedMessage
        from messages.models import Message, MessageAttachmentUpload, MessageReadReceipt, MessageReadState, Reaction
        from roles.models import Membership, PermissionOverride
        from rooms.models import Room

        user_pks = list(non_superusers.values_list("pk", flat=True))

        with transaction.atomic():
            Session.objects.all().delete()

            Reaction.objects.filter(user_id__in=user_pks).delete()
            MessageReadReceipt.objects.filter(user_id__in=user_pks).delete()
            MessageReadState.objects.filter(user_id__in=user_pks).delete()
            MessageAttachmentUpload.objects.filter(user_id__in=user_pks).delete()
            Message.objects.filter(deleted_by_id__in=user_pks).update(deleted_by=None)
            Message.objects.filter(user_id__in=user_pks).delete()

            Membership.objects.filter(user_id__in=user_pks).delete()
            PermissionOverride.objects.filter(target_user_id__in=user_pks).delete()

            Room.objects.filter(created_by_id__in=user_pks).update(created_by=None)

            Friendship.objects.filter(from_user_id__in=user_pks).delete()
            Friendship.objects.filter(to_user_id__in=user_pks).delete()

            InviteLink.objects.filter(created_by_id__in=user_pks).delete()
            JoinRequest.objects.filter(user_id__in=user_pks).delete()
            JoinRequest.objects.filter(reviewed_by_id__in=user_pks).update(reviewed_by=None)
            PinnedMessage.objects.filter(pinned_by_id__in=user_pks).update(pinned_by=None)

            AuditEvent.objects.filter(actor_user_id__in=user_pks).update(actor_user=None)
            LogEntry.objects.filter(user_id__in=user_pks).delete()

            deleted_count = non_superusers.delete()[0]

        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} users."))

        remaining = User.objects.all()
        self.stdout.write(f"Remaining: {remaining.count()}")
        for u in remaining:
            self.stdout.write(f"  {u.login} (superuser={u.is_superuser})")
