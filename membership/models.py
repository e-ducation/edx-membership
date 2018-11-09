# -*- coding: utf-8 -*-
"""
Database models for membership.
"""
from __future__ import absolute_import, unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MembershipCardInfo(models.Model):
    """ 会员卡信息 """
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    
    class Meta(object):
        verbose_name  = _('MembershipInfo')
        verbose_name_plural = verbose_name  


class MembershipOrder(models.Model):
    """ 订单 """

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(verbose_name='金额', max_digits=2)
    user = models.ForeignKey(User)
    number = models.CharField()

    class Meta(object):
        verbose_name  = _('MembershipOrder')
        verbose_name_plural = verbose_name  