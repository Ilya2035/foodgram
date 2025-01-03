"""
WSGI конфигурация для проекта Foodgram.

Этот модуль содержит WSGI-приложение, используемое для развертывания проекта.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')

application = get_wsgi_application()
