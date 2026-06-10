"""Admin auth regression tests."""

from users.models import User
from django.test import TestCase




class AdminLoginTests(TestCase):
    def test_createsuperuser_credentials_work_in_admin_login(self):
        user = User.objects.create_superuser(
            login="admin",
            email="admin@example.com",
            password="adminpass123",
        )

        response = self.client.post(
            "/admin/login/?next=/admin/",
            {
                "username": "admin",
                "password": "adminpass123",
                "next": "/admin/",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/admin/"))
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.pk))
