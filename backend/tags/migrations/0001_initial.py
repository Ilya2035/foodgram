# Generated by Django 3.2.20 on 2025-01-15 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True, verbose_name='Название тега')),
                ('slug', models.SlugField(blank=True, max_length=32, null=True, unique=True, verbose_name='Слаг')),
            ],
        ),
    ]
