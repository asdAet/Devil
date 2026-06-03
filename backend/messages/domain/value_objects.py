"""Value objects for the messages domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final
from urllib.parse import unquote

REACTION_EMOJI_MAX_LENGTH: Final = 255
CUSTOM_EMOJI_TOKEN_PREFIX: Final = "[[ce:"
CUSTOM_EMOJI_TOKEN_SUFFIX: Final = "]]"
CUSTOM_EMOJI_TOKEN_OVERHEAD: Final = len(CUSTOM_EMOJI_TOKEN_PREFIX) + len(
    CUSTOM_EMOJI_TOKEN_SUFFIX,
)
CUSTOM_EMOJI_PAYLOAD_MAX_LENGTH: Final = (
    REACTION_EMOJI_MAX_LENGTH - CUSTOM_EMOJI_TOKEN_OVERHEAD
)
UNICODE_EMOJI_MAX_LENGTH: Final = 20

# Token produced by the frontend: [[ce:${encodeURIComponent("<pack>/<file>")}]]
CUSTOM_EMOJI_TOKEN_PATTERN: Final = re.compile(
    rf"^\[\[ce:(?P<payload>(?:[A-Za-z0-9_.!~*'()-]|%[0-9A-Fa-f]{{2}})"
    rf"{{1,{CUSTOM_EMOJI_PAYLOAD_MAX_LENGTH}}})\]\]$"
)
CUSTOM_EMOJI_FILE_NAME_PATTERN: Final = re.compile(
    r"^[^/\\]+?\.(?:tgs|webm|webp)$",
    re.IGNORECASE,
)

VARIATION_SELECTOR_16: Final = "\ufe0f"
ZERO_WIDTH_JOINER: Final = "\u200d"
COMBINING_ENCLOSING_KEYCAP: Final = "\u20e3"


class ReactionEmojiError(ValueError):
    """Raised when a reaction emoji value violates the domain contract."""


def _is_in_any_range(codepoint: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= codepoint <= end for start, end in ranges)


EMOJI_BASE_RANGES: Final = (
    (0x00A9, 0x00A9),
    (0x00AE, 0x00AE),
    (0x203C, 0x203C),
    (0x2049, 0x2049),
    (0x2122, 0x2122),
    (0x2139, 0x2139),
    (0x2194, 0x21AA),
    (0x231A, 0x231B),
    (0x2328, 0x2328),
    (0x23CF, 0x23CF),
    (0x23E9, 0x23F3),
    (0x23F8, 0x23FA),
    (0x24C2, 0x24C2),
    (0x25AA, 0x25AB),
    (0x25B6, 0x25B6),
    (0x25C0, 0x25C0),
    (0x25FB, 0x25FE),
    (0x2600, 0x27BF),
    (0x2934, 0x2935),
    (0x2B05, 0x2B55),
    (0x3030, 0x3030),
    (0x303D, 0x303D),
    (0x3297, 0x3299),
    (0x1F000, 0x1FAFF),
)
EMOJI_MODIFIER_RANGE: Final = (0x1F3FB, 0x1F3FF)
KEYCAP_BASES: Final = set("#*0123456789")


def _is_standard_emoji_base(char: str) -> bool:
    return _is_in_any_range(ord(char), EMOJI_BASE_RANGES)


def _is_emoji_modifier(char: str) -> bool:
    return EMOJI_MODIFIER_RANGE[0] <= ord(char) <= EMOJI_MODIFIER_RANGE[1]


def _is_valid_unicode_emoji(value: str) -> bool:
    if not 0 < len(value) <= UNICODE_EMOJI_MAX_LENGTH:
        return False

    chars = list(value)
    has_base = False
    for index, char in enumerate(chars):
        previous = chars[index - 1] if index > 0 else ""
        next_char = chars[index + 1] if index + 1 < len(chars) else ""

        if char in KEYCAP_BASES:
            if next_char not in {VARIATION_SELECTOR_16, COMBINING_ENCLOSING_KEYCAP}:
                return False
            has_base = True
            continue

        if _is_standard_emoji_base(char):
            has_base = True
            continue

        if char == VARIATION_SELECTOR_16:
            if not previous or not (
                _is_standard_emoji_base(previous) or previous in KEYCAP_BASES
            ):
                return False
            continue

        if _is_emoji_modifier(char):
            if not previous or not _is_standard_emoji_base(previous):
                return False
            continue

        if char == ZERO_WIDTH_JOINER:
            if not previous or not next_char:
                return False
            if not (
                _is_standard_emoji_base(previous)
                or _is_emoji_modifier(previous)
                or previous == VARIATION_SELECTOR_16
            ):
                return False
            if not _is_standard_emoji_base(next_char):
                return False
            continue

        if char == COMBINING_ENCLOSING_KEYCAP:
            if previous == VARIATION_SELECTOR_16:
                previous = chars[index - 2] if index > 1 else ""
            if previous not in KEYCAP_BASES:
                return False
            continue

        return False

    return has_base


def _decode_custom_emoji_payload(payload: str) -> str:
    decoded = unquote(payload)
    if decoded == payload and "%2F" not in payload.upper():
        raise ReactionEmojiError("Custom emoji id must be URL-encoded")
    return decoded


def _validate_custom_emoji_token(value: str) -> None:
    match = CUSTOM_EMOJI_TOKEN_PATTERN.fullmatch(value)
    if not match:
        raise ReactionEmojiError("Invalid custom emoji token syntax")

    emoji_id = _decode_custom_emoji_payload(match.group("payload"))
    separator_index = emoji_id.find("/")
    if (
        separator_index <= 0
        or separator_index != emoji_id.rfind("/")
        or separator_index >= len(emoji_id) - 1
    ):
        raise ReactionEmojiError("Custom emoji id must be '<pack>/<file>'")

    pack_id = emoji_id[:separator_index]
    file_name = emoji_id[separator_index + 1:]
    if any(ord(char) < 32 for char in pack_id):
        raise ReactionEmojiError("Custom emoji pack id contains control characters")
    if "\\" in pack_id:
        raise ReactionEmojiError("Custom emoji pack id contains invalid characters")
    if any(ord(char) < 32 for char in file_name):
        raise ReactionEmojiError("Custom emoji file name contains control characters")
    if not CUSTOM_EMOJI_FILE_NAME_PATTERN.fullmatch(file_name):
        raise ReactionEmojiError("Custom emoji file name is invalid")
    if file_name in {".", ".."}:
        raise ReactionEmojiError("Custom emoji file name is invalid")


@dataclass(frozen=True, slots=True)
class ReactionEmoji:
    """Reaction emoji accepted by the chat domain."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ReactionEmojiError("Emoji cannot be empty")

        if len(self.value) > REACTION_EMOJI_MAX_LENGTH:
            raise ReactionEmojiError(f"Emoji too long: {len(self.value)} chars")

        if self.value.startswith(CUSTOM_EMOJI_TOKEN_PREFIX) or self.value.endswith(
            CUSTOM_EMOJI_TOKEN_SUFFIX
        ):
            _validate_custom_emoji_token(self.value)
            return

        if not _is_valid_unicode_emoji(self.value):
            raise ReactionEmojiError("Must be either Unicode emoji or custom emoji token")

    def __str__(self) -> str:
        return self.value

    def is_custom(self) -> bool:
        """Check if this is a custom emoji token."""
        return self.value.startswith(CUSTOM_EMOJI_TOKEN_PREFIX) and self.value.endswith(
            CUSTOM_EMOJI_TOKEN_SUFFIX
        )

    def is_unicode(self) -> bool:
        """Check if this is a Unicode emoji."""
        return not self.is_custom()
