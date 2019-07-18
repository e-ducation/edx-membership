# -*- coding:utf-8 -*-
"""
Membership Serializers
"""
from __future__ import unicode_literals
import logging
from django.utils import timezone
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.reverse import reverse

from course_api.serializers import CourseSerializer, CourseDetailSerializer
from course_modes.models import get_course_prices, CourseMode
from courseware.access import has_access
from mobile_api.users.serializers import CourseEnrollmentSerializer
from lms.djangoapps.certificates.models import certificate_status_for_student
from student.models import CourseEnrollment
from util.course import get_encoded_course_sharing_utm_params, get_link_for_about_page
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from courseware.courses import get_course_with_access

from membership.models import VIPPackage, VIPOrder, VIPInfo, VIPCoursePrice, VIPCourseEnrollment
log = logging.getLogger(__name__)


class PackageListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, info):
        return _(info.name)

    class Meta:
        model = VIPPackage
        fields = ('id', 'name', 'month', 'price', 'suggested_price',
                  'is_recommended', 'days')


class VIPOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = VIPOrder
        fields = ('status',)


class VIPInfoSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField()
    opened = serializers.SerializerMethodField()
    remain = serializers.SerializerMethodField()
    expired = serializers.SerializerMethodField()
    last_start_at = serializers.SerializerMethodField()

    def get_opened(self, info):
        delta = timezone.now().date() - info.start_at.date()
        return delta.days

    def get_remain(self, info):
        delta = info.expired_at.date() - timezone.now().date()
        return delta.days

    def get_status(self, info):
        return info.expired_at >= timezone.now()

    def get_expired(self, info):
        delta = timezone.now().date() - info.expired_at.date()
        return delta.days

    def get_last_start_at(self, info):
        """
        获取最后一次开通时间
        :param info:
        :return:
        """
        last_start_at = ''
        vip_order = VIPOrder.objects.filter(
            created_by=self.context['request'].user,
            status=VIPOrder.STATUS_SUCCESS
        ).order_by('-id').first()

        if vip_order:
            last_start_at = vip_order.start_at

        return last_start_at

    class Meta:
        model = VIPInfo
        fields = ('start_at', 'expired_at', 'status', 'opened', 'remain', 'expired', 'last_start_at')


class CourseOverviewField(serializers.RelatedField):
    """
    Custom field to wrap a CourseOverview object. Read-only.
    """

    def to_representation(self, course_overview):
        course_id = unicode(course_overview.id)
        request = self.context.get('request')
        return {
            # identifiers
            'id': course_id,
            'name': course_overview.display_name,
            'number': course_overview.display_number_with_default,
            'org': course_overview.display_org_with_default,

            # dates
            'start': course_overview.start,
            'start_display': course_overview.start_display,
            'start_type': course_overview.start_type,
            'end': course_overview.end,

            # notification info
            'subscription_id': course_overview.clean_id(padding_char='_'),

            # access info
            'courseware_access': has_access(
                request.user,
                'load_mobile',
                course_overview
            ).to_json(),

            # various URLs
            # course_image is sent in both new and old formats
            # (within media to be compatible with the new Course API)
            'media': {
                'course_image': {
                    'uri': course_overview.course_image_url,
                    'name': 'Course Image',
                }
            },
            'course_image': course_overview.course_image_url,
            'course_about': get_link_for_about_page(course_overview),
            'course_sharing_utm_parameters': get_encoded_course_sharing_utm_params(),
            'course_updates': reverse(
                'course-updates-list',
                kwargs={'course_id': course_id, 'api_version': 'v1'},
                request=request,
            ),
            'course_handouts': reverse(
                'course-handouts-list',
                kwargs={'course_id': course_id, 'api_version': 'v1'},
                request=request,
            ),
            'discussion_url': reverse(
                'discussion_course',
                kwargs={'course_id': course_id},
                request=request,
            ) if course_overview.is_discussion_tab_enabled() else None,

            'video_outline': reverse(
                'video-summary-list',
                kwargs={'course_id': course_id, 'api_version': 'v1'},
                request=request,
            ),
            'is_vip': VIPInfo.is_vip(request.user),
            'is_normal_enroll': not VIPCourseEnrollment.objects.filter(
                user=request.user,
                course_id=course_overview.id,
                is_active=True
            ).exists(),
            'has_cert': certificate_status_for_student(request.user, course_overview.id)['status'] == 'downloadable',
        }


class MobileCourseEnrollmentSerializer(CourseEnrollmentSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview", read_only=True)
    is_vip = serializers.SerializerMethodField()
    is_normal_enroll = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    def get_progress(self, model):
        
        course = get_course_with_access(model.user, 'load', model.course.id)
        course_grade = CourseGradeFactory().read(model.user, course)  

        return {
            'is_pass': course_grade.passed,
            'total_grade': course_grade.summary['percent']
        }

    def get_is_vip(self, model):
        return VIPInfo.is_vip(self.context['request'].user)

    def get_is_normal_enroll(self, model):
        vip_enroll = VIPCourseEnrollment.objects.filter(
            user=self.context['request'].user,
            course_id=model.course_id,
            is_active=True
        ).exists()

        return not vip_enroll

    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course', 'certificate',
                  'is_vip', 'is_normal_enroll', 'progress')
        lookup_field = 'username'


class MobileCourseSerializer(CourseSerializer):
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

    is_subscribe_pay = serializers.SerializerMethodField()

    def get_is_subscribe_pay(self, model):
        return VIPCoursePrice.is_subscribe_pay(model.id)


class MobileCourseDetailSerializer(CourseDetailSerializer):
    """
    Serializer for Course objects providing additional details about the
    course.

    This serializer makes additional database accesses (to the modulestore) and
    returns more data (including 'overview' text). Therefore, for performance
    and bandwidth reasons, it is expected that this serializer is used only
    when serializing a single course, and not for serializing a list of
    courses.
    """

    is_vip = serializers.SerializerMethodField()
    is_subscribe_pay = serializers.SerializerMethodField()
    course_price = serializers.SerializerMethodField()
    recommended_package = serializers.SerializerMethodField()
    has_cert = serializers.SerializerMethodField()
    is_enroll = serializers.SerializerMethodField()
    is_normal_enroll = serializers.SerializerMethodField()
    is_subscribe_pay = serializers.SerializerMethodField()
    can_free_enroll = serializers.SerializerMethodField()

    def get_is_vip(self, model):
        user = self.context['request'].user
        if user.is_authenticated():
            return VIPInfo.is_vip(self.context['request'].user)
        else:
            return False

    def get_is_subscribe_pay(self, model):
        return VIPCoursePrice.is_subscribe_pay(model.id)

    def get_course_price(self, model):
        registration_price, course_price = get_course_prices(model)
        return course_price

    def get_recommended_package(self, model):
        p = VIPPackage.recommended_package()
        return p and PackageListSerializer(p).data or None

    def get_has_cert(self, model):
        user = self.context['request'].user
        if user.is_authenticated():
            cert_status = certificate_status_for_student(
                user,
                model.id
            )['status']
            return cert_status == 'downloadable'
        else:
            return False

    def get_is_enroll(self, model):
        user = self.context['request'].user
        if user.is_authenticated():
            return True if CourseEnrollment.get_enrollment(self.context.get('request').user, model.id) else False
        else:
            return False

    def get_is_normal_enroll(self, model):
        user = self.context['request'].user
        if user.is_authenticated():
            vip_enroll = VIPCourseEnrollment.objects.filter(
                user=self.context['request'].user,
                course_id=model.id,
                is_active=True
            ).exists()
        else:
            return False

        return not vip_enroll

    def get_is_subscribe_pay(self, model):
        return VIPCoursePrice.is_subscribe_pay(model.id)

    def get_can_free_enroll(self, model):
        modes_dict = CourseMode.modes_for_course_dict(model.id)
        if CourseMode.has_professional_mode(modes_dict):
            return False
        return CourseMode.AUDIT in modes_dict or CourseMode.HONOR in modes_dict
