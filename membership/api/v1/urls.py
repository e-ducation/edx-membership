# -*- coding: utf-8 -*-
"""
URLs for membership api.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from .views import PackageListAPIView, VIPInfoAPIView, VIPOrderAPIView, VIPStatusAPIView


urlpatterns = [
    url(
        r'vip/packages$',
        PackageListAPIView.as_view(),
        name='package_list'
    ),
    url(
        r'vip/info/(?P<user>\d+)$',
        VIPInfoAPIView.as_view(),
        name='vip_info'
    ),
    url(
        r'vip/order/(?P<pk>\d+)$',
        VIPOrderAPIView.as_view(),
        name='vip_order'
    ),
    url(
        r'vip/status/(?P<user>\d+)$',
        VIPStatusAPIView.as_view(),
        name='vip_status'
    ),
]
