from rest_framework import serializers

from .models import Membership, Role


class RoleSerializer(serializers.ModelSerializer):
    room_slug = serializers.SlugRelatedField(
        source="room",
        slug_field="slug",
        read_only=True,
    )

    class Meta:
        model = Role
        fields = (
            "id",
            "room_slug",
            "name",
            "color",
            "position",
            "permissions",
            "is_default",
            "created_at",
        )
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    room_slug = serializers.SlugRelatedField(
        source="room",
        slug_field="slug",
        read_only=True,
    )
    username = serializers.SlugRelatedField(
        source="user",
        slug_field="username",
        read_only=True,
    )
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = Membership
        fields = (
            "id",
            "room_slug",
            "username",
            "nickname",
            "roles",
            "is_banned",
            "joined_at",
        )
        read_only_fields = fields
