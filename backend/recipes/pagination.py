"""
Пагинация для API.

Этот модуль содержит настройки пагинации для работы с пользователями.
"""

from rest_framework.pagination import PageNumberPagination


class PaginationforUser(PageNumberPagination):
    """
    Пагинация для пользователей.

    Определяет размер страницы, параметр запроса для изменения размера
    страницы и максимальный размер страницы.
    """

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 50
