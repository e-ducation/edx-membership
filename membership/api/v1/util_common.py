# -*- coding:utf-8 -*-
import logging
import requests
from django.conf import settings
import time

log = logging.getLogger(__name__)


def pay_result_ga(out_trade_no, el_name):
    try:
        cn = time.strftime('%Y%m%d', time.localtime(time.time()))
        google_analytics = 'http://www.google-analytics.com/collect?v=1&tid={}&cid={}&t=event&ec=vip_pay&ea=pay&el={}&cn={}&cm1=1'.format(
            settings.GOOGLE_ANALYTICS_ACCOUNT, out_trade_no, el_name, cn
        )
        log.info(google_analytics)
        r = requests.get(google_analytics)

    except Exception as ex:
        log.error(ex)
