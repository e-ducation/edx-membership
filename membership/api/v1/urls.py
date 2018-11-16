# -*- coding: utf-8 -*-
"""
URLs for membership api.
"""
from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    PackageListAPIView,
    VIPInfoAPIView,
    VIPOrderAPIView,
    VIPStatusAPIView,
    VIPPayOrderView,
    VIPPurchase,
    VIPAlipayPaying,
    VIPWechatPaying
)


urlpatterns = [
    url(
        r'vip/packages$',
        PackageListAPIView.as_view(),
        name='package_list'
    ),
    url(
        r'vip/info/$',
        VIPInfoAPIView.as_view(),
        name='vip_info'
    ),
    url(
        r'vip/order/(?P<pk>\d+)$',
        VIPOrderAPIView.as_view(),
        name='vip_order'
    ),
    url(
        r'vip/status/$',
        VIPStatusAPIView.as_view(),
        name='vip_status'
    ),
    url(
        r'vip/pay/order/$',
        VIPPayOrderView.as_view(),
        name='vip_pay_order'
    ),
    url(
        r'vip/pay/alipay/paying/$',
        VIPAlipayPaying.as_view(),
        name='vip_alipay_paying'
    ),
    url(
        r'vip/purchase/$',
        VIPPurchase.as_view(),
        name='vip_purchase'
    ),
    url(
        r'vip/pay/wechat/paying/$',
        VIPWechatPaying.as_view(),
        name='vip_wechat_paying'
    ),
]
