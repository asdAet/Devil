from users.models import User
from django.test import TestCase

from auditlog.models import AuditEvent



class AuditApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(login="audit_staff", password="pass12345", is_staff=True)
        self.member = User.objects.create_user(login="audit_member", password="pass12345")
        self.actor_one = User.objects.create_user(login="actor_one", password="pass12345")
        self.actor_two = User.objects.create_user(login="actor_two", password="pass12345")

    def test_events_endpoint_requires_staff(self):
        self.client.force_login(self.member)
        response = self.client.get("/api/admin/audit/events/")
        self.assertEqual(response.status_code, 403)

    def test_events_filters_by_user_and_action_prefix(self):
        AuditEvent.objects.create(
            action="auth.login.success",
            protocol="http",
            actor_user=self.actor_one,
            actor_user_id_snapshot=self.actor_one.pk,
            actor_username_snapshot=self.actor_one.login,
            is_authenticated=True,
            method="POST",
            path="/api/auth/login/",
            status_code=200,
            success=True,
            metadata={"room_id": 1},
        )
        AuditEvent.objects.create(
            action="auth.logout",
            protocol="http",
            actor_user=self.actor_two,
            actor_user_id_snapshot=self.actor_two.pk,
            actor_username_snapshot=self.actor_two.login,
            is_authenticated=True,
            method="POST",
            path="/api/auth/logout/",
            status_code=200,
            success=True,
            metadata={"room_id": 2},
        )

        self.client.force_login(self.staff)
        response = self.client.get(
            "/api/admin/audit/events/",
            {"actor_user_id": self.actor_one.pk, "action_prefix": "auth.login"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["action"], "auth.login.success")
        self.assertEqual(payload["items"][0]["actor"]["userId"], self.actor_one.pk)

    def test_actions_endpoint_returns_counts(self):
        AuditEvent.objects.create(
            action="auth.login.success",
            actor_user_id_snapshot=self.actor_one.pk,
            actor_username_snapshot=self.actor_one.login,
            is_authenticated=True,
            success=True,
        )
        AuditEvent.objects.create(
            action="auth.login.success",
            actor_user_id_snapshot=self.actor_one.pk,
            actor_username_snapshot=self.actor_one.login,
            is_authenticated=True,
            success=True,
        )
        AuditEvent.objects.create(
            action="auth.logout",
            actor_user_id_snapshot=self.actor_one.pk,
            actor_username_snapshot=self.actor_one.login,
            is_authenticated=True,
            success=True,
        )

        self.client.force_login(self.staff)
        response = self.client.get("/api/admin/audit/actions/", {"actor_user_id": self.actor_one.pk})
        self.assertEqual(response.status_code, 200)
        payload = response.json()["items"]
        by_action = {item["action"]: item["count"] for item in payload}
        self.assertEqual(by_action.get("auth.login.success"), 2)
        self.assertEqual(by_action.get("auth.logout"), 1)

    def test_events_endpoint_returns_400_for_invalid_filters(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/admin/audit/events/", {"limit": "0"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_event_detail_returns_404_when_missing(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/admin/audit/events/999999/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())

    def test_event_detail_returns_item_when_present(self):
        event = AuditEvent.objects.create(
            action="auth.login.success",
            actor_user_id_snapshot=self.actor_one.pk,
            actor_username_snapshot=self.actor_one.login,
            is_authenticated=True,
            success=True,
        )
        self.client.force_login(self.staff)
        response = self.client.get(f"/api/admin/audit/events/{event.pk}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["item"]
        self.assertEqual(payload["id"], event.pk)
        self.assertEqual(payload["action"], "auth.login.success")

    def test_actions_endpoint_returns_400_for_invalid_filters(self):
        self.client.force_login(self.staff)
        response = self.client.get("/api/admin/audit/actions/", {"success": "maybe"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
