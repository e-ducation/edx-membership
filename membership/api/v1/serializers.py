# -*- coding:utf-8 -*-
"""
Membership Serializers
"""
from __future__ import unicode_literals

import datetime
import pytz

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from membership.models import VIPPackage, VIPOrder, VIPInfo


class PackageListSerializer(serializers.ModelSerializer):

    class Meta:
        model = VIPPackage
        fields = ('id', 'name', 'month', 'price', 'suggested_price',
                  'is_recommended')


class VIPOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = VIPOrder
        fields = ('status',)


class VIPInfoSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()
    opened =  serializers.SerializerMethodField()
    remain = serializers.SerializerMethodField()

    def get_opened(self, info):
        today = timezone.now()
        delta = today - info.start_at
        return delta.days + 1

    def get_remain(self, info):
        today = timezone.now()
        delta = info.expired_at - today
        return delta.days

    def get_status(self, info):
        return info.expired_at >= timezone.now()

    class Meta:
        model = VIPInfo
        fields = ('start_at', 'expired_at', 'status', 'opened', 'remain')
