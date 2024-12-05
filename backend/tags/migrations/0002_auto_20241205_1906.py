from django.db import migrations


def create_default_tags(apps, schema_editor):
    Tag = apps.get_model('tags', 'Tag')

    default_tags = [
        {'name': 'Завтрак', 'slug': 'breakfast'},
        {'name': 'Обед', 'slug': 'lunch'},
        {'name': 'Ужин', 'slug': 'dinner'},
    ]

    for tag_data in default_tags:
        Tag.objects.create(**tag_data)


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_tags),
    ]
