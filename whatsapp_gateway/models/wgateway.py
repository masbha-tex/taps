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
import requests

class wApp(models.Model):
    _name = "whats.app"
    _description = "WhatsApp Gateway"

    
    url_field = fields.Char('URL', default='https://graph.facebook.com/v17.0/118373814703008/messages')
    access_token = fields.Char('Access Tocken')

    def send_message_wapp(self):
        payload = {
            "messaging_product": "whatsapp",
            "to": "8801676778656",
            "type": "template",
            "template": {
                "name": "customer_template",
            "language": {
                "code": "en_US"
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
            }
        # Make the POST request
        response = requests.post(self.url_field, json=payload, headers=headers)

        if response.status_code == 200:
        # Success: Handle the response as needed
            response_data = response.json()
        # Process the response data
        else:
        # Error: Handle the error
            error_message = response.text
        # Handle the error message
        raise UserError((error_message))