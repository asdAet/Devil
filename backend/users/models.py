# pyright: reportIncompatibleVariableOverride=false, reportCallIssue=false
"""Модели аккаунтов, профилей и публичной идентичности пользователей."""

from __future__ import annotations

import secrets
import uuid
import warnings
from pathlib import Path
from typing import ClassVar, TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.html import strip_tags
from PIL import Image

from .avatar_service import profile_avatar_upload_to

MAX_PROFILE_IMAGE_SIDE = 4096
MAX_PROFILE_IMAGE_PIXELS = MAX_PROFILE_IMAGE_SIDE * MAX_PROFILE_IMAGE_SIDE
Image.MAX_IMAGE_PIXELS = MAX_PROFILE_IMAGE_PIXELS
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
SVG_EXTENSIONS = {".svg"}
USER_PUBLIC_ID_VALIDATOR = RegexValidator(
    regex=r"^[1-9]\d{9}$",
    message="public_id must be a positive 10-digit numeric value.",
)


def generate_user_public_id() -> str:
    """Возвращает случайный публичный числовой идентификатор пользователя."""
    value = secrets.randbelow(9_000_000_000) + 1_000_000_000
    return str(value)


def normalize_user_login(login: str | None) -> str:
    """Нормализует login аккаунта к единому виду."""
    return str(login or "").strip().lower()


def normalize_user_email(email: str | None) -> str | None:
    """Нормализует email аккаунта; пустое значение хранится как NULL."""
    normalized = str(email or "").strip().lower()
    return normalized or None


class UserManager(BaseUserManager):
    """Менеджер custom user model без поля username."""

    use_in_migrations = True

    def create_user(self, login: str, email: str | None = None, password: str | None = None, **extra_fields):
        """Создает обычный аккаунт с уникальным login."""
        normalized_login = normalize_user_login(login)
        if not normalized_login:
            raise ValueError("User login must be set.")

        user = self.model(
            login=normalized_login,
            email=normalize_user_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        login: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields,
    ):
        """Создает администратора для Django Admin."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(login, email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Аккаунт пользователя. Внутренний ключ аккаунта — только id."""

    login = models.CharField(max_length=254, unique=True, db_index=True)
    email = models.EmailField(null=True, blank=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    public_id = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        validators=[USER_PUBLIC_ID_VALIDATOR],
        editable=False,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects: ClassVar[UserManager] = UserManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS: list[str] = []

    if TYPE_CHECKING:
        profile: Profile

    class Meta:
        db_table = "users_user"
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=Q(email__isnull=False),
                name="users_user_email_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["login"], name="users_user_login_idx"),
            models.Index(fields=["public_id"], name="users_user_public_id_idx"),
        ]

    def __str__(self) -> str:
        return self.login

    def clean(self):
        super().clean()
        self.login = normalize_user_login(self.login)
        self.email = normalize_user_email(self.email)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_public_id = type(self).objects.filter(pk=self.pk).values_list("public_id", flat=True).first()
            if old_public_id and old_public_id != self.public_id:
                raise ValidationError({"public_id": "public_id is immutable."})

        self.login = normalize_user_login(self.login)
        self.email = normalize_user_email(self.email)
        if not self.public_id:
            for _ in range(20):
                candidate = generate_user_public_id()
                if not type(self).objects.filter(public_id=candidate).exists():
                    self.public_id = candidate
                    break
            if not self.public_id:
                raise RuntimeError("Failed to allocate unique user public_id")

        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        profile = getattr(self, "profile", None)
        name = getattr(profile, "name", "") if profile is not None else ""
        return str(name or "").strip()

    def get_short_name(self) -> str:
        return self.get_full_name() or self.login


class Profile(models.Model):
    """Профиль пользователя: отображаемые и медиа-данные, не auth-состояние."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, blank=True, default="")
    image = models.ImageField(blank=True, upload_to=profile_avatar_upload_to)
    avatar_url = models.URLField(max_length=2048, blank=True, default="")
    avatar_crop_x = models.FloatField(null=True, blank=True)
    avatar_crop_y = models.FloatField(null=True, blank=True)
    avatar_crop_width = models.FloatField(null=True, blank=True)
    avatar_crop_height = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_image_name = self.image.name

    def __str__(self):
        user = getattr(self, "user", None)
        login = getattr(user, "login", "") if user is not None else ""
        label = self.name or login or self.user_id
        return f"{label} profile"

    def save(self, *args, **kwargs):
        if isinstance(self.bio, str):
            self.bio = strip_tags(self.bio).strip()
        if isinstance(self.name, str):
            self.name = strip_tags(self.name).strip()

        old_image_name = getattr(self, "_old_image_name", None)
        new_image_name = self.image.name if self.image else None

        if new_image_name and new_image_name != old_image_name:
            ext = Path(new_image_name).suffix or ".jpg"
            self.image.name = f"{uuid.uuid4().hex}{ext}"
            new_image_name = self.image.name

        super().save(*args, **kwargs)

        if (
            old_image_name
            and old_image_name != new_image_name
            and default_storage.exists(old_image_name)
        ):
            default_storage.delete(old_image_name)

        if not self.image or not self.image.name:
            self._old_image_name = ""
            return

        try:
            ext = Path(self.image.name or "").suffix.lower()
            if ext in SVG_EXTENSIONS:
                self._old_image_name = self.image.name
                return

            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(self.image.path) as img:
                    should_resize = (
                        img.height > MAX_PROFILE_IMAGE_SIDE
                        or img.width > MAX_PROFILE_IMAGE_SIDE
                        or (img.width * img.height) > MAX_PROFILE_IMAGE_PIXELS
                    )
                    if not should_resize:
                        self._old_image_name = self.image.name
                        return
                    img.thumbnail((MAX_PROFILE_IMAGE_SIDE, MAX_PROFILE_IMAGE_SIDE))

                    if ext in JPEG_EXTENSIONS and img.mode not in {"RGB", "L", "CMYK", "YCbCr"}:
                        img = img.convert("RGB")

                    img.save(self.image.path)
        except (
            FileNotFoundError,
            ValueError,
            OSError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            self._old_image_name = self.image.name
            return

        self._old_image_name = self.image.name


class OAuthIdentity(models.Model):
    """Внешняя OAuth-привязка к аккаунту."""

    class Provider(models.TextChoices):
        GOOGLE = "google", "Google"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oauth_identities")
    provider = models.CharField(max_length=32, choices=Provider.choices)
    provider_user_id = models.CharField(max_length=191)
    email_from_provider = models.EmailField(blank=True, default="")
    name_from_provider = models.CharField(max_length=150, blank=True, default="")
    avatar_url_from_provider = models.URLField(max_length=2048, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"],
                name="users_oauth_provider_uid_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "provider_user_id"], name="users_oauth_provider_uid_idx"),
        ]

    def __str__(self):
        return f"{self.provider}:{self.provider_user_id}"


class UserTwoFactor(models.Model):
    """TOTP two-factor state for a user account."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor")
    secret_encrypted = models.TextField(blank=True, default="")
    enabled_at = models.DateTimeField(null=True, blank=True)
    last_accepted_timestep = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id: int

    class Meta:
        indexes = [
            models.Index(fields=["enabled_at"], name="users_2fa_enabled_idx"),
        ]

    @property
    def is_enabled(self) -> bool:
        return bool(self.secret_encrypted and self.enabled_at)

    def __str__(self):
        return f"2fa:{self.user_id}:{'enabled' if self.is_enabled else 'pending'}"


class PublicHandle(models.Model):
    """Публичный @username пользователя или группы."""

    handle = models.CharField(max_length=30, unique=True, db_index=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="public_handle",
        null=True,
        blank=True,
    )
    room = models.OneToOneField(
        "rooms.Room",
        on_delete=models.CASCADE,
        related_name="public_handle",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(user__isnull=False) & Q(room__isnull=True))
                    | (Q(user__isnull=True) & Q(room__isnull=False))
                ),
                name="users_public_handle_xor_owner",
            ),
        ]

    def __str__(self):
        return f"@{self.handle}"


class SecurityRateLimitBucket(models.Model):
    """Счетчики rate limit для security/auth операций."""

    scope_key = models.CharField(max_length=191, unique=True, db_index=True)
    count = models.PositiveIntegerField(default=0)
    reset_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["reset_at"], name="users_rl_reset_idx"),
        ]

    def __str__(self):
        return f"{self.scope_key}:{self.count}"
