# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class PageDataPagination(PageNumberPagination):
    """
    pagination with extra data
    """

    def get_paginated_response(self, data, extra=None):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('extra', extra)
        ]))

