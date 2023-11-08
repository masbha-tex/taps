# # -*- coding: utf-8 -*-

from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import re
from decimal import Decimal, ROUND_HALF_UP
import decimal
from werkzeug.urls import url_encode
import logging
_logger = logging.getLogger(__name__)


import os
from twilio.rest import Client

class wApp(models.Model):
    _name = "whats.app"
    _description = "WhatsApp Gateway"

    account_sid = fields.Char(string="Account Sid")
    auth_token = fields.Char(string="Auth Tocken")


    def send_message_wapp(self)

# # Find your Account SID and Auth Token at twilio.com/console
# # and set the environment variables. See http://twil.io/secure
# account_sid = os.environ['TWILIO_ACCOUNT_SID']
# auth_token = os.environ['TWILIO_AUTH_TOKEN']
# client = Client(account_sid, auth_token)

# message = client.messages.create(
#                               from_='whatsapp:+14155238886',
#                               body='Hello, there!',
#                               to='whatsapp:+15005550006'
#                           )

# print(message.sid)