# -*- coding: utf-8 -*-
"""
URLs for membership.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from membership.views import index, card


urlpatterns = [
    url(
        r'^vip$',
        index,
        name='membership'
    ),
    url(
        r'^vip/card',
        card,
        name='membership_card'
    ),
    url(r'^api/', include('membership.api.urls')),
]
