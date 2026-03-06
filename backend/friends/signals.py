from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from chat_app_django.security.audit import audit_security_event

from .models import Friendship


def _friend_from_user_id(instance: Friendship) -> int | None:
    from_user_id = getattr(instance, "from_user_id", None)
    if from_user_id is not None:
        return int(from_user_id)
    from_user_pk = getattr(getattr(instance, "from_user", None), "pk", None)
    if from_user_pk is None:
        return None
    return int(from_user_pk)


def _friend_to_user_id(instance: Friendship) -> int | None:
    to_user_id = getattr(instance, "to_user_id", None)
    if to_user_id is not None:
        return int(to_user_id)
    to_user_pk = getattr(getattr(instance, "to_user", None), "pk", None)
    if to_user_pk is None:
        return None
    return int(to_user_pk)


@receiver(post_save, sender=Friendship)
def audit_friendship_save(sender, instance: Friendship, created: bool, **kwargs):
    from_user_id = _friend_from_user_id(instance)
    to_user_id = _friend_to_user_id(instance)
    audit_security_event(
        "friendship.created" if created else "friendship.updated",
        actor_user_id=from_user_id,
        is_authenticated=True,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        status=instance.status,
    )


@receiver(post_delete, sender=Friendship)
def audit_friendship_delete(sender, instance: Friendship, **kwargs):
    from_user_id = _friend_from_user_id(instance)
    to_user_id = _friend_to_user_id(instance)
    audit_security_event(
        "friendship.deleted",
        actor_user_id=from_user_id,
        is_authenticated=True,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
    )
