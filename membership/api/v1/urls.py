# -*- coding: utf-8 -*-
"""
URLs for membership api.
"""
from __future__ import unicode_literals

from django.conf.urls import url
from django.conf import settings

from .views import (
    PackageListAPIView,
    VIPInfoAPIView,
    VIPOrderAPIView,
    VIPPayOrderView,
    VIPPurchase,
    VIPAlipayPaying,
    VIPWechatPaying,
    MobilePackageListAPIView,
    MobilePackageListWithVIPInfoAPIView,
    MobileVIPInfoAPIView,
    MobileUserCourseEnrollmentsList,
    MobileCourseListView,
    MobileCourseDetailView,
    MobileVIPAlipayPaying,
    MobileVIPWechatPaying,
    MobileUserDetail,
    MobileUserCourseStatus,
    VIPWechatH5Paying,
    MobileVIPAppleInAppPurchase,
    MobileVIPAppleReceiptVerify,
    VIPAlipayH5Paying
)


urlpatterns = [
    url(
        r'vip/packages$',
        PackageListAPIView.as_view(),
        name='package_list'
    ),
    url(
        r'vip/info$',
        VIPInfoAPIView.as_view(),
        name='vip_info'
    ),
    url(
        r'vip/order/(?P<pk>\d+)$',
        VIPOrderAPIView.as_view(),
        name='vip_order'
    ),
    url(
        r'vip/pay/order/$',
        VIPPayOrderView.as_view(),
        name='vip_pay_order'
    ),
    url(
        r'^vip/pay/alipay/paying/$',
        VIPAlipayPaying.as_view(),
        name='vip_alipay_paying'
    ),
    url(
        r'^mobile/vip/pay/alipay/paying/$',
        MobileVIPAlipayPaying.as_view(),
        name='mobile_vip_alipay_paying'
    ),
    url(
        r'vip/purchase/$',
        VIPPurchase.as_view(),
        name='vip_purchase'
    ),
    url(
        r'^vip/pay/wechat/paying/$',
        VIPWechatPaying.as_view(),
        name='vip_wechat_paying'
    ),
    url(
        r'^mobile/vip/pay/wechat/paying/$',
        MobileVIPWechatPaying.as_view(),
        name='mobile_vip_wechat_paying'
    ),
    url(
        r'^mobile/vip/pay/apple/inapp_purchase/$',
        MobileVIPAppleInAppPurchase.as_view(),
        name='mobile_vip_pay_apple_inapppurchase'
    ),
    url(
        r'^mobile/vip/pay/apple/receipt_verify/$',
        MobileVIPAppleReceiptVerify.as_view(),
        name='mobile_vip_pay_apple_receipt_verify'
    ),
    url(
        r'mobile/vip/package/$',
        MobilePackageListAPIView.as_view(),
        name='mobile_package'
    ),
    url(
        r'mobile/vip/package/vip_info$',
        MobilePackageListWithVIPInfoAPIView.as_view(),
        name='mobile_package_with_vip_info'
    ),
    url(
        r'mobile/vip/info/$',
        MobileVIPInfoAPIView.as_view(),
        name='mobile_vip_info'
    ),
    url(
        r'mobile/users/' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        MobileUserCourseEnrollmentsList.as_view(),
        name='mobil_enrollment'
    ),
    url(
        'mobile/users/' + settings.USERNAME_PATTERN + '$',
        MobileUserDetail.as_view(),
        name='user-detail'
    ),
    url(
        '^{}/course_status_info/{}'.format(settings.USERNAME_PATTERN, settings.COURSE_ID_PATTERN),
        MobileUserCourseStatus.as_view(),
        name='user-course-status'
    ),
    url(
        r'mobile/courses/$',
        MobileCourseListView.as_view(),
        name='mobil_courses'
    ),
    url(
        r'mobile/courses/' + settings.COURSE_KEY_PATTERN + '/$',
        MobileCourseDetailView.as_view(),
        name='mobile_course_detail'
    ),
    url(
        r'vip/pay/wechat_h5/paying/$',
        VIPWechatH5Paying.as_view(),
        name='vip_wechat_paying'
    ),
    url(
        r'vip/pay/alipay_h5/paying/$',
        VIPAlipayH5Paying.as_view(),
        name='vip_alipay_h5_paying'
    )
]
