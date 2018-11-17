# -*- coding:utf-8 -*-
"""
Membership Serializers
"""
from __future__ import unicode_literals

import datetime
import pytz

from django.conf import settings
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

    def get_status(self, info):
        return info.expired_at.date() >= datetime.datetime.today().replace(tzinfo=pytz.utc).astimezone(pytz.timezone(settings.TIME_ZONE)).date()

    class Meta:
        model = VIPInfo
        fields = ('start_at', 'expired_at', 'status')
