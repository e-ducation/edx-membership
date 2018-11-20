# -*- coding:utf-8 -*-
"""
Database models for membership.
"""
from __future__ import absolute_import, unicode_literals

import logging
import pytz

from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.certificates.models import certificate_status_for_student
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class VIPInfo(models.Model):
    """ VIP card information """

    user = models.ForeignKey(User, related_name="vip_user")
    start_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()

    class Meta(object):
        app_label = 'membership'

    def new_expired_at(self, month):
        return self.expired_at + relativedelta(months=+int(month))

    @classmethod
    def get_vipinfo_for_user(cls, user):
        """
        get vip info for user
        """
        vip_info = cls.objects.filter(user=user).order_by('-id').first()
        return vip_info

    @classmethod
    def is_vip(cls, user):
        vip_info = cls.objects.filter(user=user).order_by('-id').first()
        return vip_info and vip_info.expired_at > timezone.now()

    @classmethod
    def can_view_course(cls, user, course_id):
        is_vip = cls.objects.filter(user=user).exists()
        cert_status = certificate_status_for_student(user, course_id)['status']
        
        paid_enroll = CourseEnrollment.get_enrollment(user, course_id)
        subscribe_enroll = VIPCourseEnrollment.objects.filter(user=user, course_id=course_id, is_active=True)
        enroll = paid_enroll and not subscribe_enroll

        return not (not is_vip and cert_status == 'downloadable' and not enroll)

    def __unicode__(self):
        return self.user.username


class VIPPackage(models.Model):
    """ VIP package """

    name = models.CharField(max_length=64)
    month = models.IntegerField()
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(default=0.0, decimal_places=2, max_digits=30)
    suggested_price = models.DecimalField(
        default=0.0, decimal_places=2, max_digits=30)
    is_recommended = models.BooleanField(default=False)

    class Meta(object):
        app_label = 'membership'

    def __unicode__(self):
        return self.name


class VIPOrder(models.Model):
    """ VIP order """

    STATUS_WAIT = 1  # Awaiting for payment
    STATUS_SUCCESS = 2    # Paid
    STATUS_FAILED = 3    # Cancelled
    STATUS_REFUND = 4   # Refunded

    STATUS_CHOICES = (
        (STATUS_WAIT, _(u'Awaiting for payment')),
        (STATUS_SUCCESS, _(u'Paid')),
        (STATUS_FAILED, _(u'Cancelled')),
        (STATUS_REFUND, _(u'Refunded'))
    )

    PAY_TYPE_NONE = 0  # None
    PAY_TYPE_BY_WECHAT = 1  # WeChat
    PAY_TYPE_BY_ALIPAY = 2  # Alipay
    PAY_TYPE_BY_UNIONPAY = 3  # Union pay
    PAY_TYPE_BY_APPLEPAY = 4   # Apple Pay
    PAY_TYPE_REMAIN_AMOUNT = 5  # Balance
    PAY_TYPE_NOT_ONLINE = 6  # Offline

    PAY_TYPE_CHOICES = (
        (PAY_TYPE_REMAIN_AMOUNT, _(u'Balance')),
        (PAY_TYPE_NOT_ONLINE, _(u'Offline')),
        (PAY_TYPE_BY_WECHAT, _(u'WeChat')),
        (PAY_TYPE_BY_ALIPAY, _(u'Alipay')),
        (PAY_TYPE_BY_UNIONPAY, _(u'Union pay')),
        (PAY_TYPE_BY_APPLEPAY, _(u'Apple Pay'))
    )

    name = models.CharField(max_length=64)
    month = models.IntegerField()
    trans_at = models.DateTimeField(auto_now_add=True)
    start_at = models.DateTimeField()
    expired_at = models.DateTimeField()
    status = models.IntegerField(choices=STATUS_CHOICES)
    price = models.DecimalField(default=0.0, decimal_places=2, max_digits=30)
    suggested_price = models.DecimalField(
        default=0.0, decimal_places=2, max_digits=30)
    created_by = models.ForeignKey(User, related_name="vip_order")
    description = models.CharField(max_length=255, blank=True, null=True)
    refno = models.CharField(max_length=255, blank=True, null=True)
    openid = models.CharField(max_length=128, blank=True, null=True)
    outtradeno = models.CharField(max_length=120, blank=True, null=True)
    pay_type = models.IntegerField(null=False, choices=PAY_TYPE_CHOICES)
    receipt = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)

    class Meta(object):
        app_label = 'membership'

    @classmethod
    def get_user_order(cls, order_id):
        """
        获取用户订单
        """
        order = VIPOrder.objects.filter(
            id=order_id, status=cls.STATUS_WAIT).first()
        return order

    @classmethod
    def create_order(cls, user, package_id):
        """
        创建订单
        :param user:
        :return:
        """
        order = None
        vip_package = VIPPackage.objects.filter(
            id=package_id, is_active=1).first()
        if vip_package:
            user_info = VIPInfo.get_vipinfo_for_user(user)
            if user_info:
                start_at = user_info.expired_at
                expired_at = user_info.expired_at + \
                    relativedelta(months=+int(vip_package.month))
            else:
                start_at = datetime.now(pytz.utc)
                expired_at = start_at + \
                    relativedelta(months=+int(vip_package.month))
            try:
                order = cls.objects.filter(
                    created_by=user, status=cls.STATUS_WAIT).order_by('-id')[:1].get()
                order.start_at = start_at
                order.expired_at = expired_at
                order.name = vip_package.name
                order.month = vip_package.month
                order.price = vip_package.price
                order.trans_at = datetime.now(pytz.utc)
                order.save()
            except ObjectDoesNotExist:
                order = cls.objects.create(
                    created_by=user,
                    name=vip_package.name,
                    month=vip_package.month,
                    status=cls.STATUS_WAIT,
                    start_at=start_at,
                    expired_at=expired_at,
                    pay_type=cls.PAY_TYPE_NONE,
                    price=vip_package.price
                )
            except Exception as ex:
                log.error(ex)
        return order

    @transaction.atomic
    def purchase(self, user, pay_type, description='', refno='', openid='', outtradeno='', receipt='', version='',
                 os_version=''):
        """
        purchase packages
        """

        self.status = self.STATUS_SUCCESS
        self.trans_at = datetime.now(pytz.utc)
        self.description = description
        self.refno = refno
        self.openid = openid
        self.pay_type = pay_type
        self.outtradeno = outtradeno
        self.receipt = receipt
        self.version = version
        self.os_version = os_version

        self.save()

        vip_info = VIPInfo.get_vipinfo_for_user(self.created_by)
        if vip_info:
            vip_info.expired_at = vip_info.new_expired_at(self.month)
            vip_info.save()
        else:
            expired_at = datetime.now(pytz.utc) + \
                relativedelta(months=+int(self.month))
            VIPInfo.objects.create(user=self.created_by, expired_at=expired_at)

    def __unicode__(self):
        return self.name


class VIPCourseEnrollment(models.Model):
    """ VIP user enrollment courses """

    user = models.ForeignKey(User)
    course_id = CourseKeyField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta(object):
        app_label = 'membership'

    @classmethod
    def enroll(cls, user, course_key, is_active=True):
        """
        enroll course for vip user
        """
        try:
            course = CourseOverview.get_from_id(course_key)
        except CourseOverview.DoesNotExist:
            pass

        enrollment = cls.get_or_create_enrollment(user, course_key)

        return enrollment

    @classmethod
    def get_or_create_enrollment(cls, user, course_key):
        """
        """
        assert isinstance(course_key, CourseKey)

        if user.id is None:
            user.save()

        enrollment, __ = cls.objects.get_or_create(
            user=user,
            course_id=course_key,
            defaults={
                'is_active': True
            }
        )

        return enrollment


class VIPCoursePrice(models.Model):
    """ VIP course price """

    SUBSCRIBE_NORMAL = 0
    SUBSCRIBE_PAY = 1

    SUBSCRIBE_TYPE_CHOICES = (
        (SUBSCRIBE_NORMAL, u'subscribe normal'),
        (SUBSCRIBE_PAY, u'subscribe pay'),
    )
    course_id = CourseKeyField(max_length=255, db_index=True)
    subscribe = models.IntegerField(
        default=SUBSCRIBE_NORMAL, choices=SUBSCRIBE_TYPE_CHOICES)

    class Meta(object):
        app_label = 'membership'

    @classmethod
    def get_course_subscribe_type(cls):
        """
        订阅期内课程类型（是否还需收费）
        """
        subscribe_type = {}
        for course in cls.objects.all():
            subscribe_type.setdefault(course.subscribe, []).append(course.course_id)

        return subscribe_type

    @classmethod
    def get_vip_course_price_data(cls):
        '''
        vip订阅课程类型数据
        '''
        course_prices = cls.objects.filter()
        course_price_dict = {}
        for c in course_prices:
            course_price_dict[str(c.course_id)] = int(c.subscribe)
        return course_price_dict

    @classmethod
    def is_subscribe_pay(cls, course_id):
        """
        订阅期内该课程类型，是否收费
        """
        return cls.objects.filter(course_id=course_id, subscribe=cls.SUBSCRIBE_PAY).exists()
