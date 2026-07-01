from __future__ import annotations

import asyncio
import re
import secrets
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, transaction

from rooms.models import Room

from .avatar_service import resolve_user_avatar_source
from .models import Profile, PublicHandle

HANDLE_ALLOWED_RE = re.compile(r"^[a-z][a-z0-9_]{2,29}$")
LOGIN_ALLOWED_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
PUBLIC_USER_ID_RE = re.compile(r"^[1-9]\d{9}$")
PUBLIC_GROUP_ID_RE = re.compile(r"^-[1-9]\d{9}$")
_MISSING = object()


def normalize_email(email: str | None) -> str:
    """Нормализует email к внутреннему формату приложения."""
    if not isinstance(email, str):
        return ""
    return email.strip().lower()


def normalize_login(login: str | None) -> str:
    """Нормализует login к внутреннему формату приложения."""
    if not isinstance(login, str):
        return ""
    return login.strip().lower()


def validate_login(login: str) -> str:
    """Проверяет login для обычной password-регистрации."""
    value = normalize_login(login)
    if not value:
        raise ValueError("Укажите login")
    if not LOGIN_ALLOWED_RE.fullmatch(value):
        raise ValueError("Login должен начинаться с буквы и содержать только a-z, 0-9, _ (3-64)")
    return value


def normalize_public_handle(handle: str | None) -> str:
    """Нормализует public handle к внутреннему формату приложения."""
    if not isinstance(handle, str):
        return ""
    value = handle.strip().lower()
    if value.startswith("@"):
        value = value[1:]
    return value.strip()


def validate_public_handle(handle: str) -> str:
    """Проверяет публичный @username пользователя или группы."""
    value = normalize_public_handle(handle)
    if not value:
        raise ValueError("Укажите username")
    if not HANDLE_ALLOWED_RE.fullmatch(value):
        raise ValueError("Username должен начинаться с буквы и содержать только a-z, 0-9, _ (3-30)")
    return value


def _generate_group_public_id() -> str:
    value = secrets.randbelow(9_000_000_000) + 1_000_000_000
    return f"-{value}"


def ensure_group_public_id(room: Room) -> str:
    """Гарантирует наличие immutable public_id у группы."""
    if room.public_id:
        return room.public_id
    persisted = Room.objects.filter(pk=room.pk).values_list("public_id", flat=True).first()
    if persisted:
        room.public_id = persisted
        return persisted

    if room.kind != Room.Kind.GROUP:
        raise ValueError("public_id is only supported for groups")

    for _ in range(20):
        candidate = _generate_group_public_id()
        try:
            with transaction.atomic():
                room.public_id = candidate
                room.save(update_fields=["public_id"])
                return candidate
        except IntegrityError:
            persisted = Room.objects.filter(pk=room.pk).values_list("public_id", flat=True).first()
            if persisted:
                room.public_id = persisted
                return persisted
            continue
    raise RuntimeError("Failed to allocate unique group public_id")


def ensure_profile(user) -> Profile:
    """Гарантирует наличие профиля у пользователя.

    При первичном создании профиля устанавливает полный crop (0, 0, 1, 1),
    чтобы фронтенд сразу рендерил аватарку через frame с clip-path,
    а не через object-fit: cover, который даёт смещение для дефолтного SVG.
    """
    profile = getattr(user, "profile", None)
    if profile is not None:
        _ensure_default_crop(profile)
        return profile
    profile, _ = Profile.objects.get_or_create(user=user)
    _ensure_default_crop(profile)
    return profile


def _ensure_default_crop(profile: Profile) -> None:
    """Устанавливает full crop если все crop-поля NULL."""
    if (
        profile.avatar_crop_x is not None
        or profile.avatar_crop_y is not None
        or profile.avatar_crop_width is not None
        or profile.avatar_crop_height is not None
    ):
        return
    Profile.objects.filter(pk=profile.pk).update(
        avatar_crop_x=0.0,
        avatar_crop_y=0.0,
        avatar_crop_width=1.0,
        avatar_crop_height=1.0,
    )
    profile.refresh_from_db()


def _with_sqlite_lock_retry(operation, *, attempts: int = 5):
    for attempt in range(attempts):
        try:
            return operation()
        except OperationalError as exc:
            is_last_attempt = attempt == attempts - 1
            if "locked" not in str(exc).lower() or is_last_attempt:
                raise
            time.sleep(0.05 * (attempt + 1))


def set_user_public_handle(user, handle: str | None) -> str | None:
    """Устанавливает или очищает публичный @username пользователя."""
    if handle is None or not str(handle).strip():
        _with_sqlite_lock_retry(lambda: PublicHandle.objects.filter(user=user).delete())
        return None

    normalized = validate_public_handle(str(handle))
    try:
        def _save_handle():
            with transaction.atomic():
                PublicHandle.objects.update_or_create(
                    user=user,
                    defaults={"handle": normalized, "room": None},
                )

        _with_sqlite_lock_retry(_save_handle)
    except IntegrityError as exc:
        raise ValueError("Этот username уже занят") from exc
    return normalized


def set_room_public_handle(room: Room, handle: str | None) -> str | None:
    """Устанавливает или очищает публичный @username группы."""
    if room.kind != Room.Kind.GROUP:
        raise ValueError("Handle поддерживается только для групп")

    if handle is None or not str(handle).strip():
        _with_sqlite_lock_retry(lambda: PublicHandle.objects.filter(room=room).delete())
        return None

    normalized = validate_public_handle(str(handle))
    try:
        def _save_handle():
            with transaction.atomic():
                PublicHandle.objects.update_or_create(
                    room=room,
                    defaults={"handle": normalized, "user": None},
                )

        _with_sqlite_lock_retry(_save_handle)
    except IntegrityError as exc:
        raise ValueError("Этот username уже занят") from exc
    return normalized


def _in_async_context() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _cached_related(instance: Any, relation_name: str) -> object:
    state = getattr(instance, "_state", None)
    fields_cache = getattr(state, "fields_cache", None)
    if isinstance(fields_cache, dict) and relation_name in fields_cache:
        return fields_cache[relation_name]
    return _MISSING


def _extract_handle(handle_obj: object) -> str | None:
    handle = getattr(handle_obj, "handle", None)
    if isinstance(handle, str) and handle.strip():
        return handle.strip()
    return None


def _related_public_handle(
    instance: Any,
    relation_name: str,
    *,
    allow_db_lookup: bool = True,
) -> str | None:
    cached = _cached_related(instance, relation_name)
    if cached is not _MISSING:
        return _extract_handle(cached)

    if not allow_db_lookup or _in_async_context():
        return None

    try:
        return _extract_handle(getattr(instance, relation_name, None))
    except Exception:  # noqa: BLE001
        return None


def user_public_handle(user, *, allow_db_lookup: bool = True) -> str | None:
    return _related_public_handle(
        user,
        "public_handle",
        allow_db_lookup=allow_db_lookup,
    )


def room_public_handle(room: Room, *, allow_db_lookup: bool = True) -> str | None:
    return _related_public_handle(
        room,
        "public_handle",
        allow_db_lookup=allow_db_lookup,
    )


def user_public_id(user) -> str:
    value = getattr(user, "public_id", "")
    return str(value or "").strip()


def room_public_id(room: Room) -> str:
    return ensure_group_public_id(room)


def user_public_ref(user, *, allow_db_lookup: bool = True) -> str:
    handle = user_public_handle(user, allow_db_lookup=allow_db_lookup)
    if handle:
        return f"@{handle}"
    return user_public_id(user)


def room_public_ref(room: Room, *, allow_db_lookup: bool = True) -> str:
    handle = room_public_handle(room, allow_db_lookup=allow_db_lookup)
    if handle:
        return f"@{handle}"
    return room_public_id(room)


def user_public_username(user: Any, *, allow_db_lookup: bool = True) -> str:
    """Возвращает публичное имя: handle, затем immutable public_id."""
    if user is None:
        return ""
    is_authenticated = getattr(user, "is_authenticated", False)
    if not is_authenticated:
        return ""
    if not hasattr(user, "_meta"):
        public_id = getattr(user, "public_id", None)
        if isinstance(public_id, str) and public_id.strip():
            return public_id.strip()
        login = getattr(user, "login", None)
        return login.strip() if isinstance(login, str) else ""
    if getattr(user, "pk", None) is None:
        return ""
    handle = user_public_handle(user, allow_db_lookup=allow_db_lookup)
    if handle:
        return handle
    return user_public_id(user)


def user_display_name(user: Any) -> str:
    """Возвращает отображаемое имя пользователя."""
    profile = _safe_profile(user)
    name = getattr(profile, "name", None)
    if isinstance(name, str) and name.strip():
        return name.strip()

    login = getattr(user, "login", None)
    if isinstance(login, str) and login.strip():
        return login.strip()

    return user_public_username(user)


def _safe_profile(user: Any) -> Profile | None:
    if user is None:
        return None

    try:
        profile = getattr(user, "profile", None)
    except Exception:  # noqa: BLE001
        profile = None
    if profile is not None:
        return profile

    user_pk = getattr(user, "pk", None)
    if user_pk is None or not hasattr(user, "_meta"):
        return None

    try:
        return Profile.objects.filter(user_id=user_pk).first()
    except Exception:  # noqa: BLE001
        return None


def user_profile_avatar_source(user: Any) -> str | None:
    return resolve_user_avatar_source(user)


def get_user_by_public_handle(handle: str | None):
    normalized = normalize_public_handle(handle)
    if not normalized:
        return None

    ownership = PublicHandle.objects.select_related("user").filter(handle=normalized).first()
    if ownership is not None and ownership.user is not None:
        return ownership.user
    return None


def get_room_by_public_handle(handle: str | None):
    normalized = normalize_public_handle(handle)
    if not normalized:
        return None

    ownership = PublicHandle.objects.select_related("room").filter(handle=normalized).first()
    if ownership is not None and ownership.room is not None:
        return ownership.room
    return None


def get_user_by_public_id(value: str | None):
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not PUBLIC_USER_ID_RE.fullmatch(normalized):
        return None
    User = get_user_model()
    return User.objects.select_related("profile").filter(public_id=normalized).first()


def get_room_by_public_id(value: str | None):
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not PUBLIC_GROUP_ID_RE.fullmatch(normalized):
        return None
    return Room.objects.filter(kind=Room.Kind.GROUP, public_id=normalized).first()


def normalize_public_ref(ref: str | None) -> str:
    if not isinstance(ref, str):
        return ""
    return ref.strip()


def resolve_public_ref(ref: str | None):
    normalized = normalize_public_ref(ref)
    if not normalized:
        return None, None

    if normalized.startswith("@"):
        handle = normalize_public_handle(normalized)
        ownership = PublicHandle.objects.select_related("user", "room").filter(handle=handle).first()
        if ownership is None:
            return None, None
        if ownership.user is not None:
            return "user", ownership.user
        if ownership.room is not None:
            return "group", ownership.room
        return None, None

    if PUBLIC_USER_ID_RE.fullmatch(normalized):
        user = get_user_by_public_id(normalized)
        return ("user", user) if user else (None, None)

    if PUBLIC_GROUP_ID_RE.fullmatch(normalized):
        room = get_room_by_public_id(normalized)
        return ("group", room) if room else (None, None)

    handle = normalize_public_handle(normalized)
    if HANDLE_ALLOWED_RE.fullmatch(handle):
        ownership = PublicHandle.objects.select_related("user", "room").filter(handle=handle).first()
        if ownership is None:
            return None, None
        if ownership.user is not None:
            return "user", ownership.user
        if ownership.room is not None:
            return "group", ownership.room

    return None, None
