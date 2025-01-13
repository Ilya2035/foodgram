from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TagsConfig(AppConfig):
    """Конфигурация приложения Tags."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tags'

    def ready(self):
        """Функция для создания стандартных тегов."""
        from django.db import connection
        from tags.models import Tag

        def create_default_tags(sender, **kwargs):
            if 'tags_tag' in connection.introspection.table_names():
                default_tags = [
                    {'name': 'Завтрак', 'slug': 'breakfast'},
                    {'name': 'Обед', 'slug': 'lunch'},
                    {'name': 'Ужин', 'slug': 'dinner'},
                ]
                for tag_data in default_tags:
                    Tag.objects.get_or_create(**tag_data)

        post_migrate.connect(create_default_tags, sender=self)
