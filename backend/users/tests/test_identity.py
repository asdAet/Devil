"""Coverage tests for users.identity helpers."""

from __future__ import annotations

from users.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from rooms.models import Room
from users import identity
from users.avatar_service import user_password_default_avatar_path
from users.models import Profile, PublicHandle



class UsersIdentityTests(TestCase):
    def test_normalizers_handle_non_string_and_prefix(self):
        self.assertEqual(identity.normalize_email(None), "")
        self.assertEqual(identity.normalize_email("  A@B.C "), "a@b.c")
        self.assertEqual(identity.normalize_login("  Login_1 "), "login_1")
        self.assertEqual(identity.normalize_public_handle(None), "")
        self.assertEqual(identity.normalize_public_handle("  @Alice  "), "alice")

    def test_validate_login_and_public_handle_enforce_rules(self):
        with self.assertRaises(ValueError):
            identity.validate_login("")
        with self.assertRaises(ValueError):
            identity.validate_login("1user")
        self.assertEqual(identity.validate_login("Valid_Login1"), "valid_login1")

        with self.assertRaises(ValueError):
            identity.validate_public_handle("")
        with self.assertRaises(ValueError):
            identity.validate_public_handle("ab")
        with self.assertRaises(ValueError):
            identity.validate_public_handle("bad name")
        self.assertEqual(identity.validate_public_handle("@Alice"), "alice")

    def test_user_public_username_and_display_name_priority(self):
        user = User.objects.create_user(login="fallback_user", password="pass12345")
        profile = identity.ensure_profile(user)
        profile.name = "Display Name"
        profile.save(update_fields=["name"])

        identity.set_user_public_handle(user, "publicname")
        self.assertEqual(identity.user_public_username(user), "publicname")
        self.assertEqual(identity.user_display_name(user), "Display Name")

        identity.set_user_public_handle(user, None)
        user.refresh_from_db()
        profile.name = ""
        profile.save(update_fields=["name"])
        self.assertEqual(identity.user_public_username(user), identity.user_public_id(user))
        self.assertEqual(identity.user_display_name(user), "fallback_user")

    def test_user_profile_avatar_source_returns_default_avatar_for_password_user(self):
        user = User.objects.create_user(login="default_avatar_user", password="pass12345")
        profile = identity.ensure_profile(user)
        profile.avatar_url = ""
        profile.save(update_fields=["avatar_url"])
        self.assertEqual(identity.user_profile_avatar_source(user), user_password_default_avatar_path())

    def test_get_user_by_public_handle_and_public_id(self):
        by_handle = User.objects.create_user(login="handle_lookup_user", password="pass12345")
        identity.set_user_public_handle(by_handle, "profile_handle")

        by_public_id = User.objects.create_user(login="id_lookup_user", password="pass12345")
        public_id = identity.user_public_id(by_public_id)

        self.assertEqual(identity.get_user_by_public_handle("profile_handle"), by_handle)
        self.assertEqual(identity.get_user_by_public_id(public_id), by_public_id)
        self.assertIsNone(identity.get_user_by_public_handle(""))

    def test_ensure_profile_returns_existing_or_creates_new(self):
        user = User.objects.create_user(login="profile_user", password="pass12345")
        existing = identity.ensure_profile(user)
        self.assertEqual(getattr(existing.user, "pk", None), user.pk)

        Profile.objects.filter(user=user).delete()
        user.refresh_from_db()
        recreated = identity.ensure_profile(user)
        self.assertEqual(getattr(recreated.user, "pk", None), user.pk)

    def test_user_public_id_format_and_immutability(self):
        user = User.objects.create_user(login="public_id_user", password="pass12345")
        self.assertRegex(identity.user_public_id(user), r"^[1-9]\d{9}$")

        user.public_id = "1234567891"
        with self.assertRaises(ValidationError):
            user.save(update_fields=["public_id"])

    def test_group_public_id_format_and_immutability(self):
        owner = User.objects.create_user(login="group_owner", password="pass12345")
        room = Room.objects.create(
            name="Group Room",
            kind=Room.Kind.GROUP,
            created_by=owner,
        )
        public_id = identity.ensure_group_public_id(room)
        self.assertRegex(public_id, r"^-[1-9]\d{9}$")

        room.public_id = "-1234567891"
        with self.assertRaises(ValidationError):
            room.save(update_fields=["public_id"])

    def test_public_handle_xor_owner_contract(self):
        user = User.objects.create_user(login="handle_owner", password="pass12345")
        room = Room.objects.create(name="Handle Group", kind=Room.Kind.GROUP, created_by=user)

        identity.set_user_public_handle(user, "userhandle")
        identity.set_room_public_handle(room, "roomhandle")

        self.assertEqual(PublicHandle.objects.get(user=user).handle, "userhandle")
        self.assertEqual(PublicHandle.objects.get(room=room).handle, "roomhandle")

    def test_group_public_id_created_automatically_on_group_create(self):
        owner = User.objects.create_user(login="auto_group_owner", password="pass12345")
        room = Room.objects.create(
            name="Auto Public Id Group",
            kind=Room.Kind.GROUP,
            created_by=owner,
        )
        room.refresh_from_db()
        self.assertRegex(str(room.public_id or ""), r"^-[1-9]\d{9}$")
