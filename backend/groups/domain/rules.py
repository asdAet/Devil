"""Group-specific business rules and validations."""

from __future__ import annotations

import re
import secrets
import string

from django.conf import settings

from rooms.models import Room

_INVITE_ALPHABET = string.ascii_letters + string.digits


def generate_invite_code() -> str:
    length = getattr(settings, "GROUP_INVITE_CODE_LENGTH", 12)
    return "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(length))


def validate_group_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Название группы не может быть пустым")
    if len(name) > 50:
        raise ValueError("Название группы не может превышать 50 символов")
    return name


def validate_group_username(username: str | None) -> str | None:
    if username is None or username == "":
        return None
    value = username.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]{2,29}$", value):
        raise ValueError(
            "Username должен начинаться с буквы, содержать только a-z, 0-9, _ и быть длиной 3-30"
        )
    return value


def validate_group_description(description: str) -> str:
    if len(description) > 2000:
        raise ValueError("Описание не может превышать 2000 символов")
    return description


def validate_slow_mode(seconds: int) -> int:
    if seconds < 0:
        raise ValueError("Значение медленного режима должно быть >= 0")
    if seconds > 86400:
        raise ValueError("Медленный режим не может превышать 24 часа")
    return seconds


def ensure_is_group(room: Room) -> None:
    if room.kind != Room.Kind.GROUP:
        raise ValueError("Эта операция доступна только для групп")


def generate_group_slug(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]", "-", name.strip()).strip("-").lower()
    slug = re.sub(r"-+", "-", slug)
    if len(slug) < 3:
        slug = slug + "-" + secrets.token_hex(4)
    suffix = secrets.token_hex(4)
    slug = f"g-{slug[:36]}-{suffix}"
    return slug
