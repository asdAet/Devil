from datetime import timedelta

from users.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from auditlog.models import AuditEvent



class AuditSignalsAndCleanupTests(TestCase):
    def test_cleanup_command_deletes_old_events(self):
        old_event = AuditEvent.objects.create(
            action="http.request",
            protocol="http",
            success=True,
            metadata={},
        )
        fresh_event = AuditEvent.objects.create(
            action="http.request",
            protocol="http",
            success=True,
            metadata={},
        )
        AuditEvent.objects.filter(id=old_event.pk).update(created_at=timezone.now() - timedelta(days=365))

        call_command("cleanup_audit_events", days=180)

        self.assertFalse(AuditEvent.objects.filter(id=old_event.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(id=fresh_event.pk).exists())
