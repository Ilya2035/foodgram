"""
Кастомные поля сериализаторов для работы с изображениями.

Этот модуль содержит поле Base64ImageField для
обработки изображений в формате base64.
"""

import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Кастомное поле для обработки изображений в формате Base64.

    Поддерживает декодирование изображений и сохранение их в файл.
    """

    def to_internal_value(self, data):
        """Декодирует изображение из строки Base64."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            try:
                img_data = base64.b64decode(imgstr)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Недопустимое изображение.")
            if not imghdr.what(None, img_data):
                raise serializers.ValidationError(
                    "Файл не является изображением.")
            file_name = f"{uuid.uuid4()}.{ext}"
            return ContentFile(img_data, name=file_name)
        return super().to_internal_value(data)
