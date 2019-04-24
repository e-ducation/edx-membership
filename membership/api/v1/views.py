# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging
import json
import random
import requests
import time
from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils import dateparse
from django.utils.translation import ugettext as _

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser

from rest_framework import filters
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradeAppPayModel import AlipayTradeAppPayModel
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.request.AlipayTradeAppPayRequest import AlipayTradeAppPayRequest
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest
from alipay.aop.api.domain.AlipayTradeWapPayModel import AlipayTradeWapPayModel
from course_api.views import CourseListView, CourseDetailView
from mobile_api.users.views import (
    UserCourseEnrollmentsList,
    UserCourseStatus,
    UserDetail
)

from membership.api.pagination import PageDataPagination
from membership.models import VIPOrder, VIPInfo, VIPPackage
from membership.api.v1.serializers import (
    PackageListSerializer,
    VIPOrderSerializer,
    VIPInfoSerializer,
    MobileCourseEnrollmentSerializer,
    MobileCourseSerializer,
    MobileCourseDetailSerializer)

from payments.alipay.alipay import (
    create_direct_pay_by_user,
    AlipayVerify,
    SERVER_URL,
)
from payments.alipay.app_alipay import smart_str, AlipayAppVerify
from payments.wechatpay.wxpay import (
    WxPayConf_pub,
    UnifiedOrder_pub,
    OrderQuery_pub,
    Wxpay_server_pub,
)
from payments.wechatpay.wxapp_pay import (
    WxPayConf_pub as AppWxPayConf_pub,
    UnifiedOrder_pub as AppUnifiedOrder_pub,
    OrderQuery_pub as AppOrderQuery_pub,
    Wxpay_server_pub as AppWxpay_server_pub,
    AppOrder_pub,
)
from payments.wechatpay.wxh5_pay import (
    WxH5PayConf_pub,
    UnifiedOrderH5_pub,
    OrderQueryH5_pub,
    WxpayH5_server_pub,
)
from membership.utils import (
    create_trade_id, recovery_order_id, str_to_specify_digits,
    xresult
)
from urllib import quote_plus


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

    def get(self, request, *args, **kwargs):
        '''
        套餐列表
        '''
        result = super(PackageListAPIView, self).get(request, *args, **kwargs)

        try:
            for c in result.data['results']:
                name = _(c['name'])
                c['name'] = name
        except Exception as ex:
            log.error(ex)
        return Response(xresult(data=result.data))


class VIPInfoAPIView(generics.RetrieveAPIView):
    """ 个人VIP信息 """

    serializer_class = VIPInfoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

    def get(self, request, *args, **kwargs):
        try:
            instance = VIPInfo.objects.get(user=self.request.user)
            serializer = self.get_serializer(instance)
            return Response(xresult(data=serializer.data))
        except Exception as ex:
            log.error(ex)
            return Response(xresult(data={'status': False}))


class VIPOrderAPIView(generics.RetrieveAPIView):
    """
    VIP订单状态
    """
    serializer_class = VIPOrderSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

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
            order = VIPOrder.objects.get(
                id=pk, created_by=self.request.user)
            serializer = self.get_serializer(order)

            if order.status == VIPOrder.STATUS_WAIT:
                trade_types = {
                    VIPOrder.PAY_TYPE_BY_ALIPAY: self.alipay_query,
                    VIPOrder.PAY_TYPE_BY_ALIPAY_APP: self.alipay_query,
                    VIPOrder.PAY_TYPE_BY_WECHAT: self.wechat_query,
                    VIPOrder.PAY_TYPE_BY_WECHAT_APP: self.wechat_query,
                    VIPOrder.PAY_TYPE_BY_WECHAT_H5: self.wechat_query,
                }
                if trade_types.get(order.pay_type):
                    query_resp = trade_types[order.pay_type](order.outtradeno, order.refno, order.receipt, order.pay_type)
                    if (order.status == VIPOrder.STATUS_WAIT and query_resp.get('trade_status') and
                       float(order.price) == query_resp.get('total_fee')):
                        order.purchase(
                            order.created_by,
                            order.pay_type,
                            refno=query_resp['refno']
                        )
                        log.info('********** purchase success ***********')
            return Response(xresult(data=serializer.data))
        except Exception, e:
            log.exception(e)
            return Response(xresult(code=-1, msg='query fail'))

    @classmethod
    def alipay_query(cls, out_trade_no, trade_no, receipt, trade_type):
        '''alipay query'''
        try:
            config_dict = {
                VIPOrder.PAY_TYPE_BY_ALIPAY_APP: settings.ALIPAY_APP_INFO,
                VIPOrder.PAY_TYPE_BY_ALIPAY: settings.ALIPAY_APP_INFO,
            }
            config = config_dict[trade_type]
            alipay_client_config = AlipayClientConfig()
            alipay_client_config.app_id = smart_str(config['basic_info']['APP_ID'])
            alipay_client_config.sign_type = smart_str(config['other_info']['SIGN_TYPE'])
            with open(config['basic_info']['APP_PRIVATE_KEY'], 'r') as fp:
                alipay_client_config.app_private_key = fp.read()
            client = DefaultAlipayClient(alipay_client_config=alipay_client_config)

            model = AlipayTradeQueryModel()
            model.out_trade_no = smart_str(out_trade_no)
            if trade_no:
                model.trade_no = smart_str(trade_no)
            request = AlipayTradeQueryRequest(biz_model=model)

            request_params = client.sdk_execute(request)
            resp = requests.get('{}?{}'.format(SERVER_URL, request_params)).json()
            log.info('********** alipay query result ***********')
            log.info(resp)
            query_resp = resp['alipay_trade_query_response']
            return {
                'trade_status': query_resp.get('trade_status') == 'TRADE_SUCCESS',
                'total_fee': float(query_resp.get('total_amount', 0)),
                'refno': query_resp.get('trade_no', ''),
            }
        except Exception, e:
            log.exception(e)
        return {}

    @classmethod
    def wechat_query(cls, out_trade_no, refno, receipt, trade_type):
        '''wechat query'''
        try:
            trade_types = {
                VIPOrder.PAY_TYPE_BY_WECHAT: OrderQuery_pub,
                VIPOrder.PAY_TYPE_BY_WECHAT_APP: AppOrderQuery_pub,
                VIPOrder.PAY_TYPE_BY_WECHAT_H5: OrderQueryH5_pub,
            }
            orderquery_pub = trade_types[trade_type]()
            orderquery_pub.setParameter('out_trade_no', out_trade_no)
            if refno:
                orderquery_pub.setParameter('transaction_id', refno)
            result = orderquery_pub.getResult()
            log.info('********** wechat query result ***********')
            log.info(result)
            return {
                'trade_status': (result.pop('sign') == orderquery_pub.getSign(result) and
                                 result.get('trade_state') == 'SUCCESS'),
                'total_fee': float(result.get('total_fee', 0))/100,
                'refno': result.get('transaction_id', '')
            }
        except Exception, e:
            log.exception(e)
        return {}


class VIPPayOrderView(APIView):
    """
    VIP pay order view
    参数：package_id 套餐ID
    返回: 返回order_id
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser,
    )

    def post(self, request, *args, **kwargs):
        """
        create order
        """

        package_id = request.POST.get('package_id')
        order = VIPOrder.create_order(request.user, package_id)
        return Response(xresult(data={'order_id': order.id}))


class VIPAlipayPaying(APIView):
    """
    VIP alipay paying
    参数：package_id 套餐ID
    返回: 跳转到支付宝支付页面
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser,
    )

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
        order.pay_type = VIPOrder.PAY_TYPE_BY_ALIPAY
        order.save()
        pay_html = ""
        if order:
            body = order.name
            subject = order.name
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
        try:
            log.info('********** purchase ***********')
            log.info(request.POST)

            pay_type = request.POST['trade_type']
            trade_type = self.get_trade_types()[pay_type]
            verify_srv = trade_type['verify']()
            verify_srv.saveData(json.loads(request.POST['original_data'])['data'])

            if verify_srv.checkSign():
                log.info('********** verify success ***********')
                req_data = verify_srv.getData()
                out_trade_no = req_data.get(trade_type['trade_info'][0])
                trade_no = req_data.get(trade_type['trade_info'][1])
                order_id = recovery_order_id(out_trade_no)
                order = VIPOrder.get_user_order(order_id)
                if order:
                    order.purchase(
                        order.created_by,
                        trade_type['type'],
                        refno=trade_no
                    )
                    log.info('********** purchase success ***********')
            return Response({'result': 'success'})
        except Exception, e:
            log.exception(e)
        return Response({'result': 'fail'})

    @classmethod
    def get_trade_types(cls):
        return {
            'alipay': {
                'type': VIPOrder.PAY_TYPE_BY_ALIPAY,
                'verify': AlipayVerify,
                'trade_info': ('out_trade_no', 'trade_no', 'total_fee'),
            },
            'alipay_app': {
                'type': VIPOrder.PAY_TYPE_BY_ALIPAY_APP,
                'verify': AlipayAppVerify,
                'trade_info': ('out_trade_no', 'trade_no', 'total_amount'),
            },
            'wechat': {
                'type': VIPOrder.PAY_TYPE_BY_WECHAT,
                'verify': Wxpay_server_pub,
                'trade_info': ('out_trade_no', 'transaction_id', 'total_fee'),
            },
            'wechat_app': {
                'type': VIPOrder.PAY_TYPE_BY_WECHAT_APP,
                'verify': AppWxpay_server_pub,
                'trade_info': ('out_trade_no', 'transaction_id', 'total_fee'),
            },
            'wechat_h5': {
                'type': VIPOrder.PAY_TYPE_BY_WECHAT_H5,
                'verify': WxpayH5_server_pub,
                'trade_info': ('out_trade_no', 'transaction_id', 'total_fee'),
            },
        }


class VIPWechatPaying(APIView):
    """
    vip wechat paying
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser,
    )

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
            total_fee = int(order.price * 100)

            attach_data = settings.LMS_ROOT_URL + reverse("vip_purchase")
            unifiedorder_pub.setParameter("body", order.name)
            out_trade_no = create_trade_id(order.id)
            order.pay_type = VIPOrder.PAY_TYPE_BY_WECHAT
            order.outtradeno = out_trade_no
            order.save()

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

            data = {
                'href_url': href_url,
                'order_id': order.id,
            }
            return Response(xresult(data=data))
        else:
            return Response(xresult(msg='fail', code=-1))


class MobilePackageListAPIView(generics.ListAPIView):
    """
    套餐列表
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    serializer_class = PackageListSerializer

    pagination_class = PageDataPagination

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('month',)
    ordering = ('-month',)

    def get_queryset(self):
        return VIPPackage.objects.filter(is_active=True)


class MobilePackageListWithVIPInfoAPIView(generics.ListAPIView):
    """
    会员信息和套餐列表
    """

    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    serializer_class = PackageListSerializer

    pagination_class = PageDataPagination

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('month',)
    ordering = ('-month',)

    def get_queryset(self):
        return VIPPackage.objects.filter(is_active=True)

    def get_paginated_response(self, data, extra=None):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data, extra=extra)

    def list(self, request, *args, **kwargs):
        vip_info = VIPInfo.get_vip_info_for_mobile(self.request.user)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data, extra=vip_info)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MobileVIPInfoAPIView(APIView):
    """
    会员信息
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    serializer_class = PackageListSerializer

    def get(self, request, *args, **kwargs):
        vip_info = VIPInfo.get_vip_info_for_mobile(self.request.user)

        return Response(vip_info)


class MobileUserCourseEnrollmentsList(UserCourseEnrollmentsList):
    """
    **Use Case**

        Get information about the courses that the currently signed in user is
        enrolled in.

    **Example Request**

        GET /api/mobile/v0.5/users/{username}/course_enrollments/

    **Response Values**

        If the request for information about the user is successful, the
        request returns an HTTP 200 "OK" response.

        The HTTP 200 response has the following values.

        * certificate: Information about the user's earned certificate in the
          course.
        * course: A collection of the following data about the course.

        * courseware_access: A JSON representation with access information for the course,
          including any access errors.

          * course_about: The URL to the course about page.
          * course_sharing_utm_parameters: Encoded UTM parameters to be included in course sharing url
          * course_handouts: The URI to get data for course handouts.
          * course_image: The path to the course image.
          * course_updates: The URI to get data for course updates.
          * discussion_url: The URI to access data for course discussions if
            it is enabled, otherwise null.
          * end: The end date of the course.
          * id: The unique ID of the course.
          * name: The name of the course.
          * number: The course number.
          * org: The organization that created the course.
          * start: The date and time when the course starts.
          * start_display:
            If start_type is a string, then the advertised_start date for the course.
            If start_type is a timestamp, then a formatted date for the start of the course.
            If start_type is empty, then the value is None and it indicates that the course has not yet started.
          * start_type: One of either "string", "timestamp", or "empty"
          * subscription_id: A unique "clean" (alphanumeric with '_') ID of
            the course.
          * video_outline: The URI to get the list of all videos that the user
            can access in the course.

        * created: The date the course was created.
        * is_active: Whether the course is currently active. Possible values
          are true or false.
        * mode: The type of certificate registration for this course (honor or
          certified).
        * url: URL to the downloadable version of the certificate, if exists.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    serializer_class = MobileCourseEnrollmentSerializer


class MobileCourseListView(CourseListView):
    serializer_class = MobileCourseSerializer


class MobileCourseDetailView(CourseDetailView):
    serializer_class = MobileCourseDetailSerializer


class MobileVIPAlipayPaying(APIView):
    """
    mobile VIP alipay paying
    参数：package_id 套餐ID
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

    def post(self, request, *args, **kwargs):
        try:
            package_id = request.POST.get('package_id')
            order = VIPOrder.create_order(request.user, int(package_id))
            if order:
                log.info('****** order id: {} ******'.format(order.id))
                order.pay_type = VIPOrder.PAY_TYPE_BY_ALIPAY_APP
                out_trade_no = create_trade_id(order.id)
                order.outtradeno = out_trade_no
                order.save()
                result = {'order_id': order.id}

                alipay_client_config = AlipayClientConfig()
                alipay_client_config.app_id = smart_str(settings.ALIPAY_APP_INFO['basic_info']['APP_ID'])
                alipay_client_config.sign_type = smart_str(settings.ALIPAY_APP_INFO['other_info']['SIGN_TYPE'])
                with open(settings.ALIPAY_APP_INFO['basic_info']['APP_PRIVATE_KEY'], 'r') as fp:
                    alipay_client_config.app_private_key = fp.read()

                client = DefaultAlipayClient(alipay_client_config=alipay_client_config)

                model = AlipayTradeAppPayModel()
                model.total_amount = smart_str(str_to_specify_digits(str(order.price)))
                model.product_code = smart_str("QUICK_MSECURITY_PAY")
                model.body = smart_str(order.name)
                model.subject = smart_str(order.name)
                model.out_trade_no = smart_str(out_trade_no)
                model.passback_params = smart_str(settings.LMS_ROOT_URL + reverse("vip_purchase"))

                request = AlipayTradeAppPayRequest(biz_model=model)
                request.notify_url = smart_str(settings.ALIPAY_APP_INFO['other_info']['NOTIFY_URL'])
                result['alipay_request'] = client.sdk_execute(request)

                return Response(data=result)
        except Exception, e:
            log.exception(e)
        return Response({})


class MobileVIPWechatPaying(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

    def post(self, request, *args, **kwargs):
        """
        mobile vip wechat paying
        """
        try:
            package_id = request.POST.get('package_id')
            order = VIPOrder.create_order(request.user, package_id)

            if order:
                # 获取二维码链接
                wxpayconf_pub = AppWxPayConf_pub()
                unifiedorder_pub = AppUnifiedOrder_pub()
                total_fee = int(order.price * 100)

                attach_data = settings.LMS_ROOT_URL + reverse("vip_purchase")
                unifiedorder_pub.setParameter("body", order.name)
                out_trade_no = create_trade_id(order.id)
                order.pay_type = VIPOrder.PAY_TYPE_BY_WECHAT_APP
                order.outtradeno = out_trade_no
                order.save()

                unifiedorder_pub.setParameter("out_trade_no", out_trade_no)
                unifiedorder_pub.setParameter("total_fee", str(total_fee))
                unifiedorder_pub.setParameter("notify_url", wxpayconf_pub.NOTIFY_URL)
                unifiedorder_pub.setParameter("trade_type", "APP")
                unifiedorder_pub.setParameter("attach", attach_data)

                prepay_id = unifiedorder_pub.getPrepayId()
                data = unifiedorder_pub.getUndResult()

                app_order_pub = AppOrder_pub()
                app_order_pub.setParameter('prepayid', prepay_id)
                sign, nonce_str, timestamp, wx_package = app_order_pub.get_request_params()

                result = {
                    'order_id': order.id,
                    'wechat_request': {
                        'prepay_id': prepay_id,
                        'sign': sign,
                        'appid': data['appid'],
                        'mch_id': data['mch_id'],
                        'nonce_str': nonce_str,
                        'package': wx_package,
                        'timestamp': timestamp,
                    }
                }
                return Response(result)
        except Exception, e:
            log.exception(e)
        return Response({})


class MobileVIPAppleInAppPurchase(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

    def post(self, request, *args, **kwargs):
        '''
        apple in-app purchasing
        '''
        try:
            package_id = request.POST.get('package_id')
            order = VIPOrder.create_order(request.user, package_id)
            if order:
                if order.pay_type != order.PAY_TYPE_BY_APPLE_INAPPPURCHASE:
                    order.pay_type = order.PAY_TYPE_BY_APPLE_INAPPPURCHASE
                    order.save(update_fields=['pay_type'])
                return Response({
                    'order_id': order.id
                })
        except Exception, e:
            log.exception(e)
        return Response({})


class MobileVIPAppleReceiptVerify(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )

    def post(self, request, *args, **kwargs):
        '''
        apple receipt verify
        '''
        try:
            verify_status = 1  # 0 success; 1 fail
            req_url = (settings.APPLE_VERIFY_RECEIPT_SANDBOX_URL if settings.APPLE_VERIFY_RECEIPT_IS_SANDBOX else
                       settings.APPLE_VERIFY_RECEIPT_URL)
            log.info('************ verify url *************')
            log.info(req_url)
            receipt_data = json.dumps({"receipt-data": request.POST['receipt']})
            verify_resp = requests.post(req_url, data=receipt_data).json()

            inapp_info = verify_resp['receipt']['in_app'][-1]
            if (verify_resp['status'] == 0 and
               settings.APPLE_IN_APP_PRODUCT_ID[str(request.POST['package_id'])] == inapp_info['product_id']):
                order = VIPOrder.objects.get(id=request.POST['order_id'])
                if order.status == VIPOrder.STATUS_WAIT and float(request.POST['total_fee']) == float(order.price):
                    order.purchase(
                        order.created_by,
                        VIPOrder.PAY_TYPE_BY_APPLE_INAPPPURCHASE,
                        receipt=request.POST['receipt'],
                        refno=inapp_info['transaction_id'],
                        version=request.POST.get('version', ''),
                        os_version=request.POST.get('os_version', '')
                    )
                if order.status == VIPOrder.STATUS_SUCCESS:
                    verify_status = 0
                    log.info('********* apple in-app purchase success ********')
        except Exception, e:
            log.exception(e)
        return Response({
            'status': verify_status
        })


class MobileUserDetail(UserDetail):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )


class MobileUserCourseStatus(UserCourseStatus):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )


class VIPWechatH5Paying(APIView):
    """
    vip wechat paying
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, *args, **kwargs):
        """
        生成订单 调起H5支付
        跳转到微信支付
        :param request:
        |参数|类型|是否必填|说明|：
        |package_id|int|是|套餐ID|

        ### 示例
        GET /api/v1/vip/pay/wechat_h5/paying/?package_id=1

        :return:
        |参数|类型|说明|
        |href_url|string|跳转微信支付页面链接|
        """

        package_id = request.GET.get('package_id')
        order = VIPOrder.create_order(request.user, package_id)

        if order:
            # 获取二维码链接
            wxh5payconf_pub = WxH5PayConf_pub()
            unifiedorderh5_pub = UnifiedOrderH5_pub()
            total_fee = int(order.price * 100)

            attach_data = settings.LMS_ROOT_URL + reverse("vip_purchase")
            unifiedorderh5_pub.setParameter("body", order.name)
            out_trade_no = create_trade_id(order.id)
            order.pay_type = VIPOrder.PAY_TYPE_BY_WECHAT_H5
            order.outtradeno = out_trade_no
            try:
                order.save()
                unifiedorderh5_pub.setParameter("out_trade_no", out_trade_no)
                unifiedorderh5_pub.setParameter("total_fee", str(total_fee))
                unifiedorderh5_pub.setParameter(
                    "notify_url", wxh5payconf_pub.NOTIFY_URL)
                unifiedorderh5_pub.setParameter("trade_type", "MWEB")
                unifiedorderh5_pub.setParameter("attach", attach_data)
                client_ip = unifiedorderh5_pub.get_client_ip(request)
                unifiedorderh5_pub.setParameter("spbill_create_ip", client_ip)

                prepay_id = unifiedorderh5_pub.getPrepayId()
                mweb_url = unifiedorderh5_pub.getMwebUrl()

                # 返回页面时不使用缓存
                random_str = str(random.randint(100000, 999999))
                redirect_url = settings.LMS_ROOT_URL + reverse("membership_card") + "?random=" +random_str
                mweb_url = mweb_url + "&redirect_url=" + quote_plus(redirect_url)
                data = {
                    'mweb_url': mweb_url
                }
                return Response(xresult(data=data))
            except Exception as ex:
                log.error(ex)
                return Response(xresult(msg='fail', code=-1))

        else:
            return Response(xresult(msg='fail', code=-1))


class VIPAlipayH5Paying(APIView):
    """
        VIP alipay H5 paying
        参数：package_id 套餐ID
        返回: 跳转到支付宝支付页面
        """
    """
        mobile VIP alipay paying
        参数：package_id 套餐ID
        """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, *args, **kwargs):
        try:
            package_id = request.GET.get('package_id')
            order = VIPOrder.create_order(request.user, int(package_id))
            if order:
                order.pay_type = VIPOrder.PAY_TYPE_BY_ALIPAY_APP
                out_trade_no = create_trade_id(order.id)
                order.outtradeno = out_trade_no
                order.save()
                result = {'order_id': order.id}

                alipay_client_config = AlipayClientConfig()
                alipay_client_config.app_id = smart_str(settings.ALIPAY_APP_INFO['basic_info']['APP_ID'])
                alipay_client_config.sign_type = smart_str(settings.ALIPAY_APP_INFO['other_info']['SIGN_TYPE'])
                with open(settings.ALIPAY_APP_INFO['basic_info']['APP_PRIVATE_KEY'], 'r') as fp:
                    alipay_client_config.app_private_key = fp.read()

                client = DefaultAlipayClient(alipay_client_config=alipay_client_config)

                model = AlipayTradeWapPayModel()
                model.total_amount = smart_str(str_to_specify_digits(str(order.price)))
                model.product_code = smart_str("QUICK_WAP_WAY")
                model.subject = smart_str(order.name)
                model.out_trade_no = smart_str(out_trade_no)
                # 返回页面时不使用缓存
                quit_url = settings.LMS_ROOT_URL + reverse("vip_alipay_h5_result")
                model.quit_url= smart_str(quit_url)
                model.passback_params = smart_str(settings.LMS_ROOT_URL + reverse("vip_purchase"))

                request = AlipayTradeWapPayRequest(biz_model=model)
                request.notify_url = smart_str(settings.ALIPAY_APP_INFO['other_info']['NOTIFY_URL'])
                result['alipay_request'] = client.sdk_execute(request)
                log.error(SERVER_URL + "?" + result['alipay_request'])
                data = {
                    'alipay_url': SERVER_URL + "?" + result['alipay_request'],
                    'order_id': order.id
                }
                return Response(xresult(data=data))
        except Exception, e:
            log.exception(e)
        return Response({})


class VIPAlipayH5Result(APIView):
    """
    支付宝H5购买点击完成跳转
    """
    def get(self, request, *args, **kwargs):
        """
        支付宝H5购买点击完成跳转
        """
        time.sleep(3)
        random_str = str(random.randint(100000, 999999))
        redirect_url = settings.LMS_ROOT_URL + reverse("membership_card") + "?random=" + random_str
        return HttpResponseRedirect(redirect_url)
