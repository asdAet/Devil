"""Signals for room identity invariants."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.identity import ensure_group_public_id

from .models import Room


@receiver(post_save, sender=Room)
def ensure_group_public_id_on_create(sender, instance: Room, **kwargs):
    if kwargs.get("raw", False):
        return
    if instance.kind != Room.Kind.GROUP:
        return
    if instance.public_id:
        return
    ensure_group_public_id(instance)
