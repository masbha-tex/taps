from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
from decimal import Decimal




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




class GoogleSheetConnector(models.Model):
    _name = 'google.sheet.connector'
    _rec_name= 'name'
    _description = 'Google Sheet Connector'

    name = fields.Char(string="Name")
    sprade_sheet_id = fields.Char(string="Sprade Sheet ID")
    
    def generate_google_docs(self,id):
        
        SERVICE_ACCOUNT_FILE = 'src/user/google_sheet_connector/models/mis.json'
        scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
        connect = self.env['google.sheet.connector'].search([('id','in', id)])
        for con in connect:
            ID = con.sprade_sheet_id
            
            credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
            service = build("sheets", "v4", credentials=credentials)
            sheet = service.spreadsheets()
            if con.id == 1 :
                docs = self.env['sale.order'].search([('sales_type','=', 'oa'),('state', '=','sale'),('company_id', '=',1)])
                all_orders = docs.filtered(lambda rec: not rec.last_update_gsheet or (rec.last_update_gsheet and rec.write_date > rec.last_update_gsheet))
                all_orders = sorted(all_orders, key=lambda r: r.id, reverse=False)
        
                # raise UserError((docs))
                
                for  order in all_orders:
                    
                    row_index = self.find_row_index(ID, "Sheet1", order.id)
                    
                    update_range = "Sheet1"
                    # raise UserError((row_index))
                    if row_index is not None:
                    # Update the entire row with new values
                        range_ = f'{update_range}!A{row_index}'
                        # raise UserError((range_))
                        new_values = []
                        row_values = [
                            order.id,
                            order.order_line[0].product_template_id.fg_categ_type,
                            order.name,
                            order.date_order.strftime('%d-%m-%Y'),
                            order.partner_id.name,
                            order.buyer_name.name,
                            f"{(float(order.total_product_qty)):0,.2f}",
                            f"{(float(order.avg_price)):0,.2f}",
                            f"{(float(order.amount_total)):0,.4f}",
                            order.sale_representative.name,
                            "",
                            "",
                            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            
                        ]
                        new_values.append(row_values)
                        update_body = {'values': new_values}
                        
                        try:
                            sheet.values().update(
                                spreadsheetId=ID,
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
                            order.order_line[0].product_template_id.fg_categ_type,
                            order.name,
                            order.date_order.strftime('%d-%m-%Y'),
                            order.partner_id.name,
                            order.buyer_name.name,
                            f"{(float(order.total_product_qty)):0,.2f}",
                            f"{(float(order.avg_price)):0,.2f}",
                            f"{(float(order.amount_total)):0,.4f}",
                            order.sale_representative.name,
                            "",
                            "",
                            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                        ]
                        new_values.append(row_values)
                        update_body = {'values': new_values}
            
                        try:
                            sheet.values().append(
                                spreadsheetId=ID,
                                range=update_range,
                                valueInputOption="USER_ENTERED",
                                body=update_body
                            ).execute()
                            order.write({'last_update_gsheet':datetime.now()})
                        except HttpError as e:
                            raise UserError(f"Error updating data: {e}")
                        
            if con.id == 2 :
                docs = self.env['sale.order.line'].search([('order_id.sales_type','=', 'oa'),('state', '=','sale'),('company_id', '=',3),('product_template_id.name', '!=', 'MOULD')])
                all_orders = docs.filtered(lambda rec: not rec.last_update_gsheet or (rec.last_update_gsheet and rec.write_date > rec.last_update_gsheet))
                all_orders = sorted(all_orders, key=lambda r: r.id, reverse=False)
                
                # raise UserError((all_orders))
                
                for  order in all_orders:
                    row_index = self.find_row_index(ID, "Sheet1", order.id)
                    
                    update_range = "Sheet1"
                    # raise UserError((row_index))
                    if row_index is not None:
                    # Update the entire row with new values
                        range_ = f'{update_range}!A{row_index}'
                        # raise UserError((range_))
                        new_values = []
                        row_values = [
                            order.id,
                            order.product_template_id.name,
                            order.name,
                            order.order_id.date_order.strftime('%d-%m-%Y'),
                            order.order_id.partner_id.name,
                            order.order_id.buyer_name.name,
                            f"{(float(order.product_uom_qty)):0,.2f}",
                            f"{(float(order.price_unit)):0,.2f}",
                            f"{(float(order.price_subtotal)):0,.4f}",
                            order.order_id.sale_representative.name,
                            "",
                            "",
                            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            
                        ]
                        new_values.append(row_values)
                        update_body = {'values': new_values}
                        
                        try:
                            sheet.values().update(
                                spreadsheetId=ID,
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
                            order.product_template_id.name,
                            order.order_id.name,
                            order.order_id.date_order.strftime('%d-%m-%Y'),
                            order.order_id.partner_id.name,
                            order.order_id.buyer_name.name,
                            f"{(float(order.product_uom_qty)):0,.2f}",
                            f"{(float(order.price_unit)):0,.2f}",
                            f"{(float(order.price_subtotal)):0,.4f}",
                            order.order_id.sale_representative.name,
                            "",
                            "",
                            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                        ]
                        new_values.append(row_values)
                        update_body = {'values': new_values}
            
                        try:
                            sheet.values().append(
                                spreadsheetId=ID,
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
        # raise UserError((self, spreadsheet_id, sheet_name, unique_identifier))
        
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_).execute()
        
        values = result.get('values', [])
        
        for i, row in enumerate(values, start=2):
            # raise UserError((i,row[0]))
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

    