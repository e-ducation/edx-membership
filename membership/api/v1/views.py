# -*-coding:utf-8 -*-
from __future__ import unicode_literals

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters
from rest_framework import generics
from rest_framework.views import APIView

from membership.models import VIPOrder, VIPInfo, VIPPackage
from membership.api.v1.serializers import (
    PackageListSerializer,
    VIPOrderSerializer,
    VIPInfoSerializer,
    VIPStatusSerializer
)


class VIPStatusAPIView(generics.RetrieveAPIView):

    queryset = VIPInfo.objects.all()
    serializer_class = VIPStatusSerializer
    lookup_field = 'user'

    def get_queryset(self):
        return VIPInfo.objects.filter(user=self.request.user)


class PackageListAPIView(generics.ListAPIView):
    """
    套餐列表
    """
    authentication_classes = ()
    serializer_class = PackageListSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('month',)
    ordering = ('-month',)

    def get_queryset(self):
        return VIPPackage.objects.filter(is_active=True)


class VIPInfoAPIView(generics.RetrieveAPIView):
    """ 个人VIP信息 """

    queryset = VIPInfo.objects.all()
    serializer_class = VIPInfoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)
    lookup_field = 'user'

    def get_queryset(self):
        return VIPInfo.objects.filter(user=self.request.user)


class VIPOrderAPIView(generics.RetrieveAPIView):
    """
    VIP订单状态
    """
    serializer_class = VIPOrderSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get_queryset(self):
        return VIPOrder.objects.filter(created_by=self.request.user)
