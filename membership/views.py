# -*- coding: utf-8 -*-
"""
User-facing views for the Membership app.
"""
from __future__ import absolute_import, unicode_literals

from edxmako.shortcuts import render_to_response


def index(request):
    context = {

    }
    response = render_to_response('membership/index.html', context)
    return response


def card(request):
    context = {

    }
    response = render_to_response('membership/card.html', context)
    return response
