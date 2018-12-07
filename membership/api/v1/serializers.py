# -*- coding:utf-8 -*-
"""
Membership Serializers
"""
from __future__ import unicode_literals

from django.utils import timezone

from rest_framework import serializers
from rest_framework.reverse import reverse

from lms.djangoapps.certificates.api import certificate_downloadable_status
from course_api.serializers import CourseSerializer, CourseDetailSerializer
from course_modes.models import get_course_prices
from courseware.access import has_access
from student.models import CourseEnrollment, User
from util.course import get_encoded_course_sharing_utm_params, get_link_for_about_page

from membership.models import VIPPackage, VIPOrder, VIPInfo, VIPCoursePrice


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
    opened = serializers.SerializerMethodField()
    remain = serializers.SerializerMethodField()

    def get_opened(self, info):
        today = timezone.now()
        delta = today - info.start_at
        return delta.days + 1

    def get_remain(self, info):
        today = timezone.now()
        delta = info.expired_at - today
        return delta.days

    def get_status(self, info):
        return info.expired_at >= timezone.now()

    class Meta:
        model = VIPInfo
        fields = ('start_at', 'expired_at', 'status', 'opened', 'remain')


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
                kwargs={'course_id': course_id},
                request=request,
            ),
            'course_handouts': reverse(
                'course-handouts-list',
                kwargs={'course_id': course_id},
                request=request,
            ),
            'discussion_url': reverse(
                'discussion_course',
                kwargs={'course_id': course_id},
                request=request,
            ) if course_overview.is_discussion_tab_enabled() else None,

            'video_outline': reverse(
                'video-summary-list',
                kwargs={'course_id': course_id},
                request=request,
            ),
        }


class MobileCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview", read_only=True)
    certificate = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    can_view_course = serializers.SerializerMethodField()

    def get_certificate(self, model):
        """Returns the information about the user's certificate in the course."""
        certificate_info = certificate_downloadable_status(model.user, model.course_id)
        if certificate_info['is_downloadable']:
            return {
                'url': self.context['request'].build_absolute_uri(
                    certificate_info['download_url']
                ),
            }
        else:
            return {}

    def get_is_vip(self, model):
        return VIPInfo.is_vip(self.context['request'].user)

    def get_can_view_course(self, model):
        return VIPInfo.can_view_course(
            user=self.context['request'].user,
            course_id=model.course_id
        )

    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course',
                  'certificate', 'is_vip', 'can_view_course')
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

    def get_is_vip(self, model):
        return VIPInfo.is_vip(self.context['request'].user)

    def get_is_subscribe_pay(self, model):
        return VIPCoursePrice.is_subscribe_pay(model.id)

    def get_course_price(self, model):
        registration_price, course_price = get_course_prices(model)
        return course_price

    def get_recommended_package(self, model):
        p = VIPPackage.recommended_package()
        return p and PackageListSerializer(p).data or None
