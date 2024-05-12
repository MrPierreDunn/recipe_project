from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class RecipePaginator(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = settings.PAGINATION_SIZE
