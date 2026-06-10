"""Signals for profile bootstrap and public handle snapshot synchronization."""

from __future__ import annotations

from django.conf import settings
from django.db import IntegrityError
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from chat_app_django.security.audit import audit_security_event
from messages.models import Message

from .identity import user_public_id, user_public_username
from .models import Profile, PublicHandle


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, **kwargs):
    """Гарантирует наличие Profile для каждого аккаунта."""
    if kwargs.get("raw", False):
        return
    defaults = {"name": str(getattr(instance, "login", "") or "").strip()}
    try:
        Profile.objects.get_or_create(user=instance, defaults=defaults)
    except IntegrityError:
        Profile.objects.filter(user=instance).first()


@receiver(post_save, sender=PublicHandle)
def sync_chat_handle_snapshot_on_save(sender, instance, **kwargs):
    """Обновляет username snapshot сообщений при изменении публичного handle."""
    if kwargs.get("raw", False):
        return
    user = getattr(instance, "user", None)
    if user is None:
        return

    new_username = user_public_username(user)
    Message.objects.filter(user=user).exclude(username=new_username).update(username=new_username)
    audit_security_event(
        "public_handle.user.updated",
        actor_user=user,
        actor_user_id=user.id,
        actor_username=new_username,
        is_authenticated=True,
        handle=instance.handle,
    )


@receiver(post_delete, sender=PublicHandle)
def sync_chat_handle_snapshot_on_delete(sender, instance, **kwargs):
    """Обновляет username snapshot сообщений при удалении публичного handle."""
    user = getattr(instance, "user", None)
    if user is None:
        return

    new_username = user_public_id(user)
    Message.objects.filter(user=user).exclude(username=new_username).update(username=new_username)
    audit_security_event(
        "public_handle.user.deleted",
        actor_user=user,
        actor_user_id=user.id,
        actor_username=new_username,
        is_authenticated=True,
    )
