# -*- coding: utf-8 -*-
"""
URLs for membership api.
"""
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include

urlpatterns = [
    url(r'v1/', include('membership.api.v1.urls'))
]
