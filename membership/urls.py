# -*- coding: utf-8 -*-
"""
URLs for membership.
"""
from __future__ import unicode_literals

from django.conf.urls import url, include
from membership.views import index, card, result, wechat_paying


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
    url(
        r'vip/pay/result$',
        result,
        name='vip_pay_result'
    ),
    url(
        r'vip/pay/wechat/qrcode/paying$',
        wechat_paying,
        name='vip_pay_wechat_qrcode_paying'
    ),
    url(r'^api/', include('membership.api.urls')),
]
