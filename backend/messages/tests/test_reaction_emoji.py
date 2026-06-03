"""Tests for the reaction emoji domain contract."""

from django.test import SimpleTestCase

from messages.domain import ReactionEmoji, ReactionEmojiError


class ReactionEmojiTests(SimpleTestCase):
    def test_accepts_unicode_emoji_sequences(self):
        valid_values = [
            "👍",
            "👍🏽",
            "❤️",
            "1️⃣",
            "👨‍👩‍👧‍👦",
        ]

        for value in valid_values:
            with self.subTest(value=value):
                self.assertEqual(str(ReactionEmoji(value)), value)

    def test_accepts_canonical_custom_emoji_tokens(self):
        valid_values = [
            "[[ce:Animated%2F014_5371073319107827779.tgs]]",
            "[[ce:Adaptive%2F1.webp]]",
            "[[ce:Method%2F2.webm]]",
        ]

        for value in valid_values:
            with self.subTest(value=value):
                emoji = ReactionEmoji(value)
                self.assertTrue(emoji.is_custom())
                self.assertEqual(str(emoji), value)

    def test_rejects_plain_text_and_partial_unicode_sequences(self):
        invalid_values = [
            "hello",
            "1",
            "\u200d",
            "\ufe0f",
            "👍hello",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ReactionEmojiError):
                    ReactionEmoji(value)

    def test_rejects_non_canonical_custom_emoji_tokens(self):
        invalid_values = [
            "[[ce:Animated/1.tgs]]",
            "[[ce:Animated%2F1.svg]]",
            "[[ce:Animated%2Fbad%0Aname.tgs]]",
            "[[ce:%2F1.tgs]]",
            "[[ce:Animated%2F..]]",
            "[[ce:Animated%2Fsub%2F1.tgs]]",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ReactionEmojiError):
                    ReactionEmoji(value)
