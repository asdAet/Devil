"""Authentication backend for login/email + password accounts."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q

from .identity import normalize_email, normalize_login


class LoginOrEmailBackend(BaseBackend):
    """Authenticates a custom user by login or email."""

    def authenticate(self, request=None, username=None, password=None, **kwargs):
        raw_identifier = kwargs.get("identifier", username)
        identifier = str(raw_identifier or "").strip()
        if not identifier or not password:
            return None

        normalized = normalize_email(identifier) if "@" in identifier else normalize_login(identifier)
        if not normalized:
            return None

        User = get_user_model()
        user = (
            User.objects.filter(Q(login=normalized) | Q(email=normalized))
            .select_related("profile")
            .first()
        )
        if user is None or not user.is_active:
            return None
        if not user.check_password(password):
            return None
        return user

    def get_user(self, user_id):
        User = get_user_model()
        return User.objects.filter(pk=user_id).first()
