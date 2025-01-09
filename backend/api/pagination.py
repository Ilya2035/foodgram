from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE_USERS

class PaginationForUser(PageNumberPagination):
    """
    Пагинация для пользователей.

    Определяет размер страницы и параметр
    запроса для изменения размера страницы.
    """

    page_size = PAGE_SIZE_USERS
    page_size_query_param = 'limit'
