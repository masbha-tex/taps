from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby





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




class SaleOrder(models.Model):
    _name = 'google.sheet.connector'
    _description = 'Google Sheet Connector'

    scope = fields.Char(string="Scope")
    sprade_sheet_id = fields.Char(string="Sprade Sheet ID")
    
    def generate_google_docs(self):
        SERVICE_ACCOUNT_FILE = 'src/user/google_sheet_connector/models/cred_service.json'
        scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()
        # result = (sheet.values().get(spreadsheetId=self.sprade_sheet_id, range="Sheet1!A1:B2").execute())
        # values = result.get("values", [])
        # raise UserError((date.today().strftime('%d-%m-%Y')))
        # data = ['1']
        docs = self.env['sale.order'].search([('sales_type','=', 'oa'),('company_id', '=',1)],limit=50)
        all_orders = docs.filtered(lambda rec: not rec.last_update_gsheet or (rec.last_update_gsheet and rec.write_date > rec.last_update_gsheet))


        
        for  order in all_orders:
            row_index = self.find_row_index(self.sprade_sheet_id, "Sheet1", order.id)
            update_range = "Sheet1"
            # raise UserError((row_index))
            if row_index is not None:
            # Update the entire row with new values
                range_ = f'{update_range}!A{row_index}'
                # raise UserError((range_))
                new_values = []
                row_values = [
                    order.id,
                    order.order_line[0].product_template_id.name,
                    order.name,
                    order.partner_id.name,
                    order.buyer_name.name,
                    float(order.total_product_qty),
                    float(order.avg_price),
                    float(order.amount_total),
                    order.sale_representative.name,
                    (date.today().strftime('%d-%m-%Y')),
                    
                ]
                new_values.append(row_values)
                update_body = {'values': new_values}
                
                try:
                    sheet.values().update(
                        spreadsheetId=self.sprade_sheet_id,
                        range=range_,
                        valueInputOption="USER_ENTERED",
                        body=update_body
                    ).execute()
                    order.write({'last_update_gsheet':datetime.now()})
                except HttpError as e:
                    raise UserError(f"Error updating data: {e}")
    
            if row_index is None:
                update_range = "Sheet1"
                new_values = []
                row_values = [
                    order.id,
                    order.order_line[0].product_template_id.name,
                    order.name,
                    order.partner_id.name,
                    order.buyer_name.name,
                    float(order.total_product_qty),
                    float(order.avg_price),
                    float(order.amount_total),
                    order.sale_representative.name,
                    (date.today().strftime('%d-%m-%Y')),
                ]
                new_values.append(row_values)
                update_body = {'values': new_values}
    
                try:
                    sheet.values().append(
                        spreadsheetId=self.sprade_sheet_id,
                        range=update_range,
                        valueInputOption="USER_ENTERED",
                        body=update_body
                    ).execute()
                    order.write({'last_update_gsheet':datetime.now()})
                except HttpError as e:
                    raise UserError(f"Error updating data: {e}")
                
                
            
    def find_row_index(self, spreadsheet_id, sheet_name, id):
        
        row_index = self.find_row_index_in_sheet(spreadsheet_id, sheet_name, id)
        # raise UserError((row_index))
        return row_index

    def find_row_index_in_sheet(self, spreadsheet_id, sheet_name, unique_identifier):
        # Example: Assume column A contains the unique identifier, and we want to find the row index based on that
        
        range_ = f'{sheet_name}!A2:A'
        service = self.get_sheets_service()
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_).execute()
        values = result.get('values', [])
        
        for i, row in enumerate(values, start=2):
            # raise UserError((row, row[0],i))
            if  row and int(row[0]) == unique_identifier:
                
                return i

        return None
    def get_sheets_service(self):
        # Load credentials from the credentials JSON file
        SERVICE_ACCOUNT_FILE = 'src/user/google_sheet_connector/models/cred_service.json'
        scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        service = build('sheets', 'v4', credentials=credentials)
        return service

    