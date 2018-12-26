# -*- coding: utf-8 -*-
"""
User-facing views for the Membership app.
"""
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from edxmako.shortcuts import render_to_response
from utils import recovery_order_id
from util.cache import cache_if_anonymous


@cache_if_anonymous()
def index(request):
    context = {

    }
    response = render_to_response('membership/index.html', context)
    return response


@login_required
def card(request):
    context = {

    }
    response = render_to_response('membership/card.html', context)
    return response


def result(request):
    """
    订单支付结果
    out_trade_no 订单请求交易号，需要按规则，返回order_id
    """
    out_trade_no = request.GET.get("out_trade_no", "")
    context = {
        "order_id": recovery_order_id(out_trade_no)
    }
    response = render_to_response('membership/result.html', context)
    return response


def wechat_paying(request):
    """
    微信扫码支付
    code_url: 生成的二维码
    order_id: 订单ID
    price: 订单价格
    """
    code_url = request.GET.get("code_url", "")
    order_id = request.GET.get("order_id", "")
    price = request.GET.get("price", "")

    context = {
        "code_url": code_url,
        "order_id": order_id,
        "price": price,
    }
    response = render_to_response('membership/wechat_paying.html', context)
    return response
