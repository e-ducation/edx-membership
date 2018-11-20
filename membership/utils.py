# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
import decimal
import random

from pytz import UTC
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler


def create_trade_id(pid):
    """
    返回一个唯一数
    :param pid:
    :return:
    """
    cur_datetime = datetime.datetime.now(UTC).strftime('%Y%m%d%H%M%S')
    rand_num = random.randint(1000, 9999)
    mch_vno = cur_datetime + str(rand_num) + str(pid)
    return mch_vno


def recovery_order_id(out_trade_id):
    """
    获取原始的订单号
    :param out_trade_id:
    :return:
    """
    out_trade_id_str = str(out_trade_id)
    if out_trade_id and len(out_trade_id_str) > 18:
        oid = out_trade_id_str[18:len(out_trade_id_str)]
    else:
        oid = "0"
    return oid


def str_to_specify_digits(str, digits_length=2):
    """
    把字符串转换成指定小数位
    :param str:
    :param digits_length:
    :return:
    """
    try:
        digits_str = '0.{digits}'.format(digits=digits_length * '0')
        result_str = decimal.Decimal(str).quantize(decimal.Decimal(digits_str))
        return result_str
    except Exception as ex:
        return str


def xresult(code=0, msg='', data=None):
    # TODO 异常错误补充
    ERROR_CODES = {}
    msg = ERROR_CODES.get(code) if code in ERROR_CODES else msg

    return {
        'code': code,
        'data': data,
        'msg': msg
    }


def customer_exception_handler(exc, context):
    '''
    drf 异常处理
    '''
    if isinstance(exc, exceptions.NotAuthenticated):
        return Response(xresult(code=-1, msg=exc.detail))
    return exception_handler(exc)
