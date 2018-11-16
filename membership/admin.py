# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from membership.models import (
    VIPCourseEnrollment,
    VIPCoursePrice,
    VIPInfo,
    VIPOrder,
    VIPPackage
)


@admin.register(VIPCourseEnrollment)
class VIPCourseEnrollmentAdmin(admin.ModelAdmin):

    search_fields = ('course_id',)

    list_display = (
        'id',
        'user',
        'course_id',
        'created_at',
        'is_active'
    )


@admin.register(VIPCoursePrice)
class VIPCoursePriceAdmin(admin.ModelAdmin):

    search_fields = ('course_id',)

    list_display = (
        'id',
        'course_id',
        'subscribe'
    )


@admin.register(VIPInfo)
class VIPInfoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'start_at',
        'expired_at'
    )


@admin.register(VIPPackage)
class VIPPackageAdmin(admin.ModelAdmin):

    search_fields = ('name',)

    list_display = (
        'id',
        'name',
        'month',
        'is_active',
        'price',
        'suggested_price',
        'is_recommended'
    )


@admin.register(VIPOrder)
class VIPOrderAdmin(admin.ModelAdmin):

    search_fields = ('name', 'created_by')

    list_display = (
        'id',
        'name',
        'month',
        'trans_at',
        'start_at',
        'expired_at',
        'status',
        'price',
        'suggested_price',
        'created_by',
        'refno',
        'outtradeno',
        'pay_type'
    )
