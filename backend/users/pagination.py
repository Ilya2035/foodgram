"""
Кастомная пагинация для приложения Users.

Этот модуль содержит класс для настройки пагинации.
"""

from rest_framework.pagination import PageNumberPagination


class PaginationforUser(PageNumberPagination):
    """
    Кастомный класс пагинации для пользователей.

    Атрибуты:
        page_size: Количество объектов на странице.
        page_size_query_param: Параметр
        запроса для указания количества объектов.
        max_page_size: Максимальное количество объектов на странице.
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 50
