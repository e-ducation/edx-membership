# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser

from rest_framework import filters
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
from payments.alipay.alipay import create_direct_pay_by_user
from payments.alipay.app_alipay import create_app_pay_by_user
from payments.wechatpay.wxpay import (
    WxPayConf_pub,
    UnifiedOrder_pub,
    OrderQuery_pub,
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

    def get(self, request, *args, **kwargs):
        '''
        套餐列表
        '''
        result = super(PackageListAPIView, self).get(request, *args, **kwargs)
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
            expired = timezone.now() - instance.expired_at
            # 已过期
            if expired.days > 0:
                data = {
                    'status': False,
                    'expired': expired.days,
                    'start_at': instance.start_at,
                    'expired_at': instance.expired_at
                }
                return Response(xresult(data=data))
            else:
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

    WECHAT_PAY_STATUS = {
        'NOTPAY': VIPOrder.STATUS_WAIT,
        'SUCCESS': VIPOrder.STATUS_SUCCESS,
        'REVOKED': VIPOrder.STATUS_FAILED,
        'REFUND': VIPOrder.STATUS_REFUND
    }

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
                if order.pay_type == VIPOrder.PAY_TYPE_BY_WECHAT:
                    serializer.data['status'] = self.wechatpay_query(order)

            return Response(xresult(data=serializer.data))
        except Exception, e:
            log.error(e)
            return Response(xresult(code=-1, msg='query fail'))

    @classmethod
    def wechatpay_query(cls, order):
        '''
        查询微信支付订单状态
        '''
        orderquery_pub = OrderQuery_pub()
        orderquery_pub.setParameter('out_trade_no', order.outtradeno)
        if order.refno:
            orderquery_pub.setParameter('transaction_id', order.refno)
        result = orderquery_pub.getResult()
        # 验签
        if result.pop('sign') == orderquery_pub.getSign(result):
            return cls.WECHAT_PAY_STATUS.get(result['trade_state'], 0)
        return 0


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
        return Response(xresult(data={'order_id': order.id}))


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
        order.pay_type = VIPOrder.PAY_TYPE_BY_ALIPAY
        order.save()
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
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    serializer_class = MobileCourseSerializer


class MobileCourseDetailView(CourseDetailView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
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
            order.pay_type = VIPOrder.PAY_TYPE_BY_ALIPAY
            order.save()

            extra_common_param = settings.LMS_ROOT_URL + reverse("vip_purchase")
            total_fee = str_to_specify_digits(str(order.price))
            trade_id = create_trade_id(order.id)

            result = {'order_id': order.id}
            if order:
                body = "BUY {amount} RMB ".format(amount=order.price)
                subject = "BUY VIP"
                total_fee = order.price
                result['data_url'] = create_app_pay_by_user(trade_id, subject, body, str(total_fee), extra_common_param)

            return Response(data=result)
        except Exception, e:
            log.exception(e)
        return Response({})


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
