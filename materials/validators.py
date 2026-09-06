import re

from rest_framework import serializers

YOUTUBE_URL_PATTERN = r"^https?://(www\.)?youtube\.com(/.*)?$"


def validate_youtube_url(value):
    """Разрешает сохранять только ссылки на youtube.com."""
    if value and not re.match(YOUTUBE_URL_PATTERN, value):
        raise serializers.ValidationError(
            "Разрешены ссылки только на youtube.com."
        )
