import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Поле для работы с изображениями в формате base64.

    Позволяет декодировать строку изображения в файл для сохранения.
    """

    def to_internal_value(self, data):
        """
        Преобразует входные данные в объект файла изображения.

        Если данные представлены в формате base64, они декодируются и
        преобразуются в объект ContentFile с уникальным именем файла.

        Аргументы:
            data (str): Входные данные изображения.

        Возвращает:
            Объект файла изображения.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            img_data = base64.b64decode(imgstr)
            ext = imghdr.what(None, img_data)
            if ext is None:
                raise serializers.ValidationError(
                    'Невалидный формат изображения'
                )
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(img_data, name=filename)
        return super().to_internal_value(data)
