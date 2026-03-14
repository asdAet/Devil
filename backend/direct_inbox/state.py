"""Cache-backed unread/active state for direct messages."""

from __future__ import annotations

from typing import Any

from django.core.cache import cache


UNREAD_KEY_PREFIX = "direct:unread"
ACTIVE_KEY_PREFIX = "direct:active"
USER_GROUP_PREFIX = "direct_inbox_user_"


def user_group_name(user_id: int) -> str:
    return f"{USER_GROUP_PREFIX}{int(user_id)}"


def unread_key(user_id: int) -> str:
    return f"{UNREAD_KEY_PREFIX}:{int(user_id)}"


def active_key(user_id: int) -> str:
    return f"{ACTIVE_KEY_PREFIX}:{int(user_id)}"


def _normalize_room_ids(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    seen: set[int] = set()
    result: list[int] = []
    for item in value:
        try:
            room_id = int(item)
        except (TypeError, ValueError):
            continue
        if room_id <= 0 or room_id in seen:
            continue
        seen.add(room_id)
        result.append(room_id)
    return result


def _normalize_counts(value: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    if isinstance(value, dict):
        for key, raw in value.items():
            try:
                room_id = int(key)
                count = int(raw)
            except (TypeError, ValueError):
                continue
            if room_id <= 0 or count <= 0:
                continue
            result[str(room_id)] = count
        return result
    if isinstance(value, list):
        for room_id in _normalize_room_ids(value):
            result[str(room_id)] = 1
    return result


def _counts_to_room_ids(counts: dict[str, int]) -> list[int]:
    result: list[int] = []
    for key in counts.keys():
        try:
            room_id = int(key)
        except (TypeError, ValueError):
            continue
        if room_id > 0:
            result.append(room_id)
    return result


def _parse_positive_room_id(value: int | str | None) -> int | None:
    if isinstance(value, int):
        room_id = value
    elif isinstance(value, str):
        try:
            room_id = int(value)
        except ValueError:
            return None
    else:
        return None

    if room_id <= 0:
        return None
    return room_id


def get_unread_room_ids(user_id: int) -> list[int]:
    counts = _normalize_counts(cache.get(unread_key(user_id)))
    return _counts_to_room_ids(counts)

def get_unread_state(user_id: int) -> dict[str, Any]:
    counts = _normalize_counts(cache.get(unread_key(user_id)))
    room_ids = _counts_to_room_ids(counts)
    return {
        "dialogs": len(room_ids),
        "roomIds": room_ids,
        "counts": counts,
    }


def mark_unread(user_id: int, room_id: int | str | None, ttl_seconds: int) -> dict[str, Any]:
    normalized_room_id = _parse_positive_room_id(room_id)
    if normalized_room_id is None:
        return get_unread_state(user_id)

    current = _normalize_counts(cache.get(unread_key(user_id)))
    key = str(normalized_room_id)
    current[key] = current.get(key, 0) + 1
    cache.set(unread_key(user_id), current, timeout=ttl_seconds)
    room_ids = _counts_to_room_ids(current)
    return {
        "dialogs": len(room_ids),
        "roomIds": room_ids,
        "counts": current,
    }


def mark_read(user_id: int, room_id: int | str | None, ttl_seconds: int) -> dict[str, Any]:
    normalized_room_id = _parse_positive_room_id(room_id)
    if normalized_room_id is None:
        return get_unread_state(user_id)

    current = _normalize_counts(cache.get(unread_key(user_id)))
    current.pop(str(normalized_room_id), None)
    if current:
        cache.set(unread_key(user_id), current, timeout=ttl_seconds)
    else:
        cache.delete(unread_key(user_id))
    room_ids = _counts_to_room_ids(current)
    return {
        "dialogs": len(room_ids),
        "roomIds": room_ids,
        "counts": current,
    }


def set_active_room(user_id: int, room_id: int, conn_id: str, ttl_seconds: int) -> None:
    cache.set(
        active_key(user_id),
        {
            "roomId": int(room_id),
            "connId": conn_id,
        },
        timeout=ttl_seconds,
    )


def touch_active_room(user_id: int, conn_id: str, ttl_seconds: int) -> None:
    value = cache.get(active_key(user_id))
    if not isinstance(value, dict):
        return
    if value.get("connId") != conn_id:
        return
    cache.set(active_key(user_id), value, timeout=ttl_seconds)


def clear_active_room(user_id: int, conn_id: str | None = None) -> None:
    if conn_id is None:
        cache.delete(active_key(user_id))
        return
    value = cache.get(active_key(user_id))
    if not isinstance(value, dict):
        return
    if value.get("connId") != conn_id:
        return
    cache.delete(active_key(user_id))


def is_room_active(user_id: int, room_id: int) -> bool:
    value = cache.get(active_key(user_id))
    if not isinstance(value, dict):
        return False
    room_id_value = value.get("roomId")
    if room_id_value is None:
        return False
    try:
        return int(room_id_value) == int(room_id)
    except (TypeError, ValueError):
        return False
