# -*-coding:utf-8 -*-
from __future__ import unicode_literals
import logging
import json
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect
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
from payments.alipay.alipay import create_direct_pay_by_user
from payments.wechatpay.wxpay import (
    Common_util_pub,
    WxPayConf_pub,
    Wxpay_client_pub,
    UnifiedOrder_pub,
    NativeCall_pub,
    NativeLink_pub,
    Wxpay_server_pub,
    Notify_pub,
    OrderQuery_pub
)
from membership.utils import create_trade_id, recovery_order_id, str_to_specify_digits

log = logging.getLogger(__name__)


class VIPStatusAPIView(generics.RetrieveAPIView):

    queryset = VIPInfo.objects.all()
    serializer_class = VIPStatusSerializer

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


class VIPPayOrderView(APIView):
    """
    VIP pay order view
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
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        create order
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

        return HttpResponseRedirect(pay_html)

    def get_pay_html(self, body, subject, total_fee, http_host, order_id):
        """
        get alipay html
        """
        # 支付信息，订单号必须唯一。
        # 以下包含的内容替换为实际的内容。
        # params = {
        # 'out_trade_no': order_id,
        # 'subject': subject,
        # 'body': body[0:len(body) - 1],
        # 'total_fee': str(total_fee)
        # }
        # 及时到帐
        # tn 请与贵网站订单系统中的唯一订单号匹配 subject 订单名称，显示在支付宝收银台里的“商品名称”里，显示在支付宝的交易管理的“商品名称”的列表里。
        # body 订单描述、订单详细、订单备注，显示在支付宝收银台里的“商品描述”里 price 订单总金额，显示在支付宝收银台里的“应付总额”里
        # 担保交易
        # payhtml=create_partner_trade_by_buyer(order_id_str, body, subject, total_fee)
        # if len(str(total_fee)) > 0 and total_fee != 0:
        #    total_fee = int(str(total_fee)[0]) * 0.01
        # else:
        #    total_fee = 0.01
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
        order_id = recovery_order_id(out_trade_no)
        trade_no = request.POST.get("trade_no")

        # TODO : 需要根据 响应body 进行付款类型的判断
        pay_type = request.POST.get("trade_type")
        order = VIPOrder.get_user_order(order_id)

        print '%' * 100
        print order_id
        print order 
        print '%' * 100
        if order and order.status == VIPOrder.STATUS_WAIT:
            order.purchase(order.created_by, pay_type,
                           outtradeno=out_trade_no, refno=trade_no)
        return Response({'result': 'success'})


class VIPWechatPaying(APIView):
    """
    vip wechat paying 
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        生成订单 生成二维码
        生成二维码
        模式二与模式一相比，流程更为简单，不依赖设置的回调支付URL。商户后台系统先调用微信支付的统一下单接口，
        微信后台系统返回链接参数code_url，商户后台系统将code_url值生成二维码图片，用户使用微信客户端扫码后发起支付。
        注意：code_url有效期为2小时，过期后扫码不能再发起支付。
        统一下单接口:
        除被扫支付场景以外，商户系统先调用该接口在微信支付服务后台生成预支付交易单，
        返回正确的预支付交易回话标识后再按扫码、JSAPI、APP等不同场景生成交易串调起支付
        以下字段在return_code 和result_code都为SUCCESS的时候有返回
        交易类型	 trade_type
        预支付交易会话标识	 prepay_id
        二维码链接 code_url
        :param request:
        :return:
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
            unifiedorder_pub.setParameter("notify_url", wxpayconf_pub.NOTIFY_URL)
            unifiedorder_pub.setParameter("trade_type", "NATIVE")
            unifiedorder_pub.setParameter("attach", attach_data)

            code_url = unifiedorder_pub.getCodeUrl()

            return Response({'result': 'success', 'code': '200', 'code_url': code_url, 'order_id': order.id})
        else:
            return Response({'result': 'failed', 'code': '500'})
