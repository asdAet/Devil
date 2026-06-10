# pyright: reportAttributeAccessIssue=false
"""Содержит тесты модуля `test_forms` подсистемы `users`."""


import io
from unittest.mock import patch

from PIL import Image
from users.models import User
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from django.test import TestCase
from django.utils.datastructures import MultiValueDict

from users.forms import ProfileUpdateForm, UserUpdateForm
from users.models import MAX_PROFILE_IMAGE_SIDE



class UserUpdateFormTests(TestCase):
    """Группирует тестовые сценарии класса `UserUpdateFormTests`."""
    def test_allows_same_login_for_current_user(self):
        """Проверяет сценарий `test_allows_same_login_for_current_user`."""
        user = User.objects.create_user(login='user1', password='pass12345')
        form = UserUpdateForm(data={'login': 'user1', 'email': ''}, instance=user)
        self.assertTrue(form.is_valid())

    def test_rejects_duplicate_login(self):
        """Проверяет сценарий `test_rejects_duplicate_login`."""
        User.objects.create_user(login='user1', password='pass12345')
        user2 = User.objects.create_user(login='user2', password='pass12345')
        form = UserUpdateForm(data={'login': 'user1', 'email': ''}, instance=user2)
        self.assertFalse(form.is_valid())
        self.assertIn('login', form.errors)

    def test_login_length_boundary(self):
        """Проверяет граничные значения длины login в форме аккаунта."""
        user = User.objects.create_user(login='base_user', password='pass12345')

        valid_form = UserUpdateForm(data={'login': 'x' * 64, 'email': ''}, instance=user)
        self.assertTrue(valid_form.is_valid())

        invalid_form = UserUpdateForm(data={'login': 'x' * 65, 'email': ''}, instance=user)
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('login', invalid_form.errors)

    def test_rejects_duplicate_email_case_insensitive(self):
        """Проверяет сценарий `test_rejects_duplicate_email_case_insensitive`."""
        User.objects.create_user(login='user1', password='pass12345', email='mail@example.com')
        user2 = User.objects.create_user(login='user2', password='pass12345', email='other@example.com')
        form = UserUpdateForm(data={'login': 'user2', 'email': 'MAIL@example.com'}, instance=user2)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProfileUpdateFormTests(TestCase):
    """Группирует тестовые сценарии класса `ProfileUpdateFormTests`."""
    @staticmethod
    def _image_upload(size=(20, 20)) -> SimpleUploadedFile:
        """Создает тестовую PNG-картинку заданного размера."""
        image = Image.new("RGB", size, (10, 20, 30))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile("avatar.png", buffer.read(), content_type="image/png")

    @staticmethod
    def _svg_upload(*, with_script: bool = False) -> SimpleUploadedFile:
        if with_script:
            payload = (
                b"<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'>"
                b"<script>alert('x')</script></svg>"
            )
        else:
            payload = (
                b"<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20'>"
                b"<rect width='20' height='20' fill='red'/></svg>"
            )
        return SimpleUploadedFile("avatar.svg", payload, content_type="image/svg+xml")

    @staticmethod
    def _files(image: UploadedFile) -> MultiValueDict[str, UploadedFile]:
        return MultiValueDict({"image": [image]})

    def test_clean_bio_strips_html_tags(self):
        """Проверяет сценарий `test_clean_bio_strips_html_tags`."""
        user = User.objects.create_user(login='bio_user', password='pass12345')
        profile = user.profile
        form = ProfileUpdateForm(
            data={'bio': '<b>Hello</b> <script>alert(1)</script>'},
            instance=profile,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['bio'], 'Hello alert(1)')

    def test_clean_image_rejects_too_large_dimensions(self):
        """Отклоняет изображение, если хотя бы одна сторона превышает лимит."""
        user = User.objects.create_user(login="image_too_large", password="pass12345")
        form = ProfileUpdateForm(
            data={"bio": "ok"},
            files=self._files(self._image_upload(size=(MAX_PROFILE_IMAGE_SIDE + 1, 100))),
            instance=user.profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_clean_image_rejects_decompression_bomb(self):
        """Отклоняет изображение при срабатывании защиты PIL от bomb-архивов."""
        user = User.objects.create_user(login="bomb_image", password="pass12345")
        with patch("users.forms.Image.open", side_effect=Image.DecompressionBombError):
            form = ProfileUpdateForm(
                data={"bio": "ok"},
                files=self._files(self._image_upload(size=(20, 20))),
                instance=user.profile,
            )
            self.assertFalse(form.is_valid())
            self.assertIn("image", form.errors)

    def test_clean_image_accepts_safe_svg(self):
        user = User.objects.create_user(login="svg_image_ok", password="pass12345")
        form = ProfileUpdateForm(
            data={"bio": "ok"},
            files=self._files(self._svg_upload()),
            instance=user.profile,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_image_rejects_svg_with_script(self):
        user = User.objects.create_user(login="svg_image_bad", password="pass12345")
        form = ProfileUpdateForm(
            data={"bio": "ok"},
            files=self._files(self._svg_upload(with_script=True)),
            instance=user.profile,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_accepts_complete_avatar_crop_payload(self):
        """Сохраняет валидный набор crop-метаданных аватарки."""
        user = User.objects.create_user(login="crop_ok", password="pass12345")
        form = ProfileUpdateForm(
            data={
                "bio": "ok",
                "avatarCropX": "0.1",
                "avatarCropY": "0.2",
                "avatarCropWidth": "0.3",
                "avatarCropHeight": "0.4",
            },
            instance=user.profile,
        )

        self.assertTrue(form.is_valid())
        profile = form.save()
        self.assertEqual(profile.avatar_crop_x, 0.1)
        self.assertEqual(profile.avatar_crop_y, 0.2)
        self.assertEqual(profile.avatar_crop_width, 0.3)
        self.assertEqual(profile.avatar_crop_height, 0.4)

    def test_rejects_partial_avatar_crop_payload(self):
        """Отклоняет неполный набор crop-метаданных."""
        user = User.objects.create_user(login="crop_partial", password="pass12345")
        form = ProfileUpdateForm(
            data={
                "bio": "ok",
                "avatarCropX": "0.1",
                "avatarCropY": "0.2",
            },
            instance=user.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_rejects_out_of_bounds_avatar_crop_payload(self):
        """Отклоняет crop-метаданные, выходящие за границы изображения."""
        user = User.objects.create_user(login="crop_bad", password="pass12345")
        form = ProfileUpdateForm(
            data={
                "bio": "ok",
                "avatarCropX": "0.8",
                "avatarCropY": "0.2",
                "avatarCropWidth": "0.4",
                "avatarCropHeight": "0.4",
            },
            instance=user.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)
