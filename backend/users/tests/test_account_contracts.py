"""Architecture contracts for account and public identity boundaries."""

from collections.abc import Mapping
from typing import Any, cast

from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase

from messages.models import Message
from messages.serializers import MessageSerializer
from rooms.models import Room
from users.identity import set_user_public_handle, user_public_id
from users.models import User


def _fieldset_fields(fieldsets) -> set[str]:
    return {
        field
        for _title, options in fieldsets
        for field in options.get("fields", ())
        if isinstance(field, str)
    }


class AccountArchitectureContractTests(TestCase):
    def test_user_model_and_admin_do_not_expose_technical_username(self):
        with self.assertRaises(FieldDoesNotExist):
            User._meta.get_field("username")

        model_admin = cast(Any, admin.site._registry[User])
        configured_fields = {
            *model_admin.list_display,
            *model_admin.search_fields,
            *_fieldset_fields(model_admin.fieldsets),
            *_fieldset_fields(model_admin.add_fieldsets),
        }

        self.assertNotIn("username", configured_fields)
        self.assertNotIn("user__username", configured_fields)

    def test_project_admins_do_not_reference_legacy_user_username_field(self):
        project_apps = {"users", "groups", "roles", "messages", "rooms", "friends"}
        checked_attrs = ("search_fields", "list_display", "list_filter", "ordering", "raw_id_fields")

        legacy_refs = []
        for model, model_admin in admin.site._registry.items():
            if model._meta.app_label not in project_apps:
                continue

            for attr_name in checked_attrs:
                for value in getattr(model_admin, attr_name, ()) or ():
                    if isinstance(value, str) and "__username" in value:
                        legacy_refs.append(f"{model._meta.label}.{attr_name}:{value}")

        self.assertEqual(legacy_refs, [])

    def test_message_public_identity_never_exposes_private_login(self):
        user = User.objects.create_user(login="private_login", password="pass12345")
        room = Room.objects.create(name="Public", kind=Room.Kind.PUBLIC)
        message = Message.objects.create(
            username="stale_snapshot",
            user=user,
            room=room,
            message_content="hello",
        )

        set_user_public_handle(user, "public_handle")
        message.refresh_from_db()
        with_handle = cast(Mapping[str, object], MessageSerializer(message).data)

        self.assertEqual(message.username, "public_handle")
        self.assertEqual(with_handle["publicRef"], "@public_handle")
        self.assertEqual(with_handle["username"], "public_handle")
        self.assertNotIn(user.login, (with_handle["publicRef"], with_handle["username"]))

        set_user_public_handle(user, None)
        user.refresh_from_db()
        message.refresh_from_db()
        without_handle = cast(Mapping[str, object], MessageSerializer(message).data)
        public_id = user_public_id(user)

        self.assertEqual(message.username, public_id)
        self.assertEqual(without_handle["publicRef"], public_id)
        self.assertEqual(without_handle["username"], public_id)
        self.assertNotIn(user.login, (without_handle["publicRef"], without_handle["username"]))
