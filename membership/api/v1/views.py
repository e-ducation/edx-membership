# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from rest_framework import filters
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from membership.models import VIPOrder, VIPInfo, VIPPackage
from membership.api.v1.serializers import (
    PackageListSerializer,
    VIPOrderSerializer,
    VIPInfoSerializer
)
from payments.alipay.alipay import create_direct_pay_by_user
from payments.wechatpay.wxpay import (
    WxPayConf_pub,
    UnifiedOrder_pub,
)
from membership.utils import (
    create_trade_id, recovery_order_id, str_to_specify_digits,
    xresult
)

log = logging.getLogger(__name__)


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

    serializer_class = VIPInfoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, *args, **kwargs):
        try:
            instance = VIPInfo.objects.get(user=self.request.user)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as ex:
            return Response(json.dumps({'status': False}))


class VIPOrderAPIView(generics.RetrieveAPIView):
    """
    VIP订单状态
    """
    serializer_class = VIPOrderSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, pk, *args, **kwargs):
        """
        查询订单状态详情
        |参数|类型|是否必填|说明|：
        |id|int|是|订单ID|

        ### 示例
        GET /api/v1/vip/order/1

        :return:
        |参数|类型|说明|
        |status|int|订单详情 1: 等待支付, 2: 已完成, 3: 已取消, 4: 已退款, 0: 查询失败|
        """
        try:
            instance = VIPOrder.objects.get(
                id=pk, created_by=self.request.user)
            serializer = self.get_serializer(instance)
            return Response(xresult(data=serializer.data))
        except Exception, e:
            log.error(e)
            return Response(xresult(code=-1, msg='query fail'))


class VIPPayOrderView(APIView):
    """
    VIP pay order view
    参数：package_id 套餐ID
    返回: 返回order_id
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        create order
        """

        package_id = request.POST.get('package_id')
        order = VIPOrder.create_order(request.user, package_id)
        return Response(json.dumps({'order_id': order.id}))


class VIPAlipayPaying(APIView):
    """
    VIP alipay paying
    参数：package_id 套餐ID
    返回: 跳转到支付宝支付页面
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        VIP alipay paying
        参数：package_id 套餐ID
        :param request:
        |参数|类型|是否必填|说明|：
        |package_id|int|是|套餐ID|

        ### 示例
        GET /api/v1/vip/pay/alipay/paying/?package_id=1

        :return:
        |参数|类型|说明|
        |alipay_url|string|跳转到支付宝支付页面|
        |order_id|int|订单id|
        """
        package_id = request.GET.get('package_id')
        order = VIPOrder.create_order(request.user, package_id)
        pay_html = ""
        if order:
            body = "BUY {amount} RMB ".format(amount=order.price)
            subject = "BUY VIP"
            total_fee = order.price
            http_host = request.META.get("HTTP_HOST")

            pay_html = self.get_pay_html(
                body, subject, total_fee, http_host, order.id)

        data = {
            'alipay_url': pay_html,
            'order_id': order.id
        }
        return Response(xresult(data=data))

    def get_pay_html(self, body, subject, total_fee, http_host, order_id):
        """
        get alipay html
        # 支付信息，订单号必须唯一
        """
        extra_common_param = settings.LMS_ROOT_URL + reverse("vip_purchase")
        total_fee = str_to_specify_digits(str(total_fee))
        trade_id = create_trade_id(order_id)
        pay_html = create_direct_pay_by_user(
            trade_id,
            body,
            subject,
            total_fee,
            http_host,
            extra_common_param=extra_common_param
        )
        return pay_html


class VIPPurchase(APIView):
    """
    VIP purchase
    """

    def post(self, request, *args, **kwargs):
        """
        支付成功之后，接受payments app回调，进行业务逻辑的处理
        """

        out_trade_no = request.POST.get("out_trade_no", "")
        trade_no = request.POST.get("trade_no")
        pay_type = request.POST.get("trade_type")

        # TODO : 需要根据 响应body 进行付款类型的判断
        order_pay_types = {
            'alipay': VIPOrder.PAY_TYPE_BY_ALIPAY,
            'wechat': VIPOrder.PAY_TYPE_BY_WECHAT
        }

        order_id = recovery_order_id(out_trade_no)
        order = VIPOrder.get_user_order(order_id)
        if order and order.status == VIPOrder.STATUS_WAIT:
            order.purchase(
                order.created_by,
                order_pay_types.get(pay_type),
                outtradeno=out_trade_no,
                refno=trade_no
            )
        return Response({'result': 'success'})


class VIPWechatPaying(APIView):
    """
    vip wechat paying
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        生成订单 生成微信支付二维码
        二维码链接 code_url
        跳转到微信支付二维码页面 href_url
        :param request:
        |参数|类型|是否必填|说明|：
        |package_id|int|是|套餐ID|

        ### 示例
        GET /api/v1/vip/pay/wechat/paying/?package_id=1

        :return:
        |参数|类型|说明|
        |href_url|string|跳转微信支付页面链接|
        """

        package_id = request.GET.get('package_id')
        order = VIPOrder.create_order(request.user, package_id)

        if order:
            # 获取二维码链接
            wxpayconf_pub = WxPayConf_pub()
            unifiedorder_pub = UnifiedOrder_pub()
            # TODO
            body = 'wechat vip'
            total_fee = int(order.price * 100)

            attach_data = settings.LMS_ROOT_URL + reverse("vip_purchase")
            unifiedorder_pub.setParameter("body", body)
            out_trade_no = create_trade_id(order.id)
            unifiedorder_pub.setParameter("out_trade_no", out_trade_no)
            unifiedorder_pub.setParameter("total_fee", str(total_fee))
            unifiedorder_pub.setParameter(
                "notify_url", wxpayconf_pub.NOTIFY_URL)
            unifiedorder_pub.setParameter("trade_type", "NATIVE")
            unifiedorder_pub.setParameter("attach", attach_data)

            code_url = unifiedorder_pub.getCodeUrl()
            para_str = "?code_url={}&order_id={}&price={}".format(
                code_url, order.id, order.price)
            href_url = settings.LMS_ROOT_URL + \
                reverse("vip_pay_wechat_qrcode_paying") + para_str
            return Response({'result': 'success', 'code': '200', 'href_url': href_url})
        else:
            return Response({'result': 'failed', 'code': '500'})
