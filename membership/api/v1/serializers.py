# -*- coding:utf-8 -*-
"""
Membership Serializers
"""
from __future__ import unicode_literals

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
        import datetime
        return info.expired_at > datetime.datetime.today().date()

    class Meta:
        model = VIPInfo
        fields = ('start_at', 'expired_at', 'status')


class VIPStatusSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()

    def get_status(self, info):
        import datetime
        return info.expired_at > datetime.datetime.today().date()

    class Meta:
        model = VIPInfo
        fields = ('status', )
