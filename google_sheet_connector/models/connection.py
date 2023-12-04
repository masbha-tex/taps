from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
from decimal import Decimal



from google.auth import external_account
from odoo import models, fields, api
import os
# import gspread
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from odoo.exceptions import AccessError, UserError, ValidationError
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from gspread_dataframe import set_with_dataframe



class GoogleSheetConnector(models.Model):
    _name = 'google.sheet.connector'
    _rec_name= 'name'
    _description = 'Google Sheet Connector'

    name = fields.Char(string="Name")
    sprade_sheet_id = fields.Char(string="Sprade Sheet ID")
    
    def generate_google_docs(self,id,limit):
        
        SERVICE_ACCOUNT_FILE = 'src/user/google_sheet_connector/models/mis.json'
        scope = [
                    'https://spreadsheets.google.com/feeds', 
                    'https://www.googleapis.com/auth/drive'
                ]
        connect = self.env['google.sheet.connector'].search([('id','=', id)])
        
        ID = connect.sprade_sheet_id
        
        # credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        # service = build("sheets", "v4", credentials=credentials)
        # sheet = service.spreadsheets()
        credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        gc = gspread.authorize(credentials)
        worksheet_name = 'Sheet1'  
            # Open the Google Spreadsheet using its title
        worksheet = gc.open_by_key(ID).worksheet(worksheet_name)


        if id == 1:
            # Fetch data from the Odoo model (sale.order in this case)
            sale_orders = self.env['sale.order'].sudo().search([('sales_type','=', 'oa'),('state', '=','sale'),('company_id', '=',1)],limit=limit)
            sale_orders = sorted(sale_orders, key=lambda r: r.id, reverse=False)
            

            # Create a DataFrame from the Odoo records
            data = {'ID': [order.id for order in sale_orders],
                    'PRODUCT CATEGORY': [order.order_line[0].product_template_id.fg_categ_type for order in sale_orders],
                    'OA NUMBER': [order.name for order in sale_orders],
                    'OA DATE': [order.date_order.date() for order in sale_orders],
                    'CUSTOMER': [order.partner_id.name for order in sale_orders],
                    'BUYER': [order.buyer_name.name for order in sale_orders],
                    'QTY(Pcs)': [order.total_product_qty for order in sale_orders],
                    'AVERAGE PRICE($)': [order.avg_price for order in sale_orders],
                    'TOTAL VALUE($)': [order.amount_total for order in sale_orders],
                    'SALES REPRESENTATIVE': [order.sale_representative.name for order in sale_orders],
                    'CLOSING DATE': [order.closing_date if order.closing_date else '' for order in sale_orders],
                    'DELIVERY DATE': [order.pr_delivery_date if order.pr_delivery_date else '' for order in sale_orders],
                    'LAST UPDATE': [date.today() for order in sale_orders]
                   }
                    
            df = pd.DataFrame(data)

            # Update the worksheet with the data
            # worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            set_with_dataframe(worksheet, df)
        
                    
        if id == 2:
            # Fetch data from the Odoo model (sale.order in this case)
            sale_orders_line = self.env['sale.order.line'].sudo().search([('order_id.sales_type','=', 'oa'),('state', '=','sale'),('company_id', '=',3),('product_template_id.name', '!=', 'MOULD'),('product_template_id', 'in', ['t','f'])],limit=limit)
            sale_orders_line = sorted(sale_orders_line, key=lambda r: r.id, reverse=False)

            # Create a DataFrame from the Odoo records
            data = {'ID': [order.id for order in sale_orders_line],
                    'PRODUCT': [order.product_template_id.name for order in sale_orders_line],
                    'OA NUMBER': [order.order_id.name for order in sale_orders_line],
                    'OA DATE': [order.order_id.date_order.date() for order in sale_orders_line],
                    'CUSTOMER': [order.order_id.partner_id.name for order in sale_orders_line],
                    'BUYER': [order.order_id.buyer_name.name for order in sale_orders_line],
                    'QTY(Gross)': [order.product_uom_qty for order in sale_orders_line],
                    'UNIT PRICE($)': [order.price_unit for order in sale_orders_line],
                    'TOTAL VALUE($)': [order.price_subtotal for order in sale_orders_line],
                    'SALES REPRESENTATIVE': [order.order_id.sale_representative.name for order in sale_orders_line],
                    'CLOSING DATE': [order.order_id.closing_date if order.order_id.closing_date else '' for order in sale_orders_line],
                    'DELIVERY DATE': [order.order_id.pr_delivery_date if order.order_id.pr_delivery_date else '' for order in sale_orders_line],
                    'LAST UPDATE': [date.today() for order in sale_orders_line]
                   }
                    
            df = pd.DataFrame(data)

            # Update the worksheet with the data
            # worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            set_with_dataframe(worksheet, df)
        