"""Serializers for friend management HTTP API."""

from __future__ import annotations

from rest_framework import serializers

from friends.models import Friendship


def _friend_to_user_id(obj: Friendship) -> int:
    to_user_id = getattr(obj, "to_user_id", None)
    if to_user_id is not None:
        return int(to_user_id)
    to_user_pk = getattr(getattr(obj, "to_user", None), "pk", None)
    if to_user_pk is None:
        raise ValueError("Friendship recipient id is missing")
    return int(to_user_pk)


def _friend_from_user_id(obj: Friendship) -> int:
    from_user_id = getattr(obj, "from_user_id", None)
    if from_user_id is not None:
        return int(from_user_id)
    from_user_pk = getattr(getattr(obj, "from_user", None), "pk", None)
    if from_user_pk is None:
        raise ValueError("Friendship sender id is missing")
    return int(from_user_pk)


class _UserBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class FriendOutputSerializer(serializers.ModelSerializer):
    """Serializes an accepted friendship — shows the friend (to_user)."""

    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ("id", "user", "created_at")

    def get_user(self, obj: Friendship) -> dict:
        return {"id": _friend_to_user_id(obj), "username": obj.to_user.username}


class IncomingRequestOutputSerializer(serializers.ModelSerializer):
    """Serializes incoming pending request — shows who sent it (from_user)."""

    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ("id", "user", "created_at")

    def get_user(self, obj: Friendship) -> dict:
        return {"id": _friend_from_user_id(obj), "username": obj.from_user.username}


class OutgoingRequestOutputSerializer(serializers.ModelSerializer):
    """Serializes outgoing pending request — shows target (to_user)."""

    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ("id", "user", "created_at")

    def get_user(self, obj: Friendship) -> dict:
        return {"id": _friend_to_user_id(obj), "username": obj.to_user.username}


class UsernameInputSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
