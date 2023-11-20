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
        result = (sheet.values().get(spreadsheetId=self.sprade_sheet_id, range="Sheet1!A1:B2").execute())
        values = result.get("values", [])
        # raise UserError((values))
        # data = ['1']
        docs = self.env['sale.order'].search([('sales_type','=', 'oa')], limit=1)
        asif=1
        (sheet.values().update(spreadsheetId=self.sprade_sheet_id, range="Sheet1!A3", valueInputOption="USER_ENTERED", body={"values": [[docs.order_line[0].product_template_id.name]]}).execute())
        (sheet.values().update(spreadsheetId=self.sprade_sheet_id, range="Sheet1!B3", valueInputOption="USER_ENTERED", body={"values": [[docs.name]]}).execute())
        (sheet.values().update(spreadsheetId=self.sprade_sheet_id, range="Sheet1!C3", valueInputOption="USER_ENTERED", body={"values": [[docs.partner_id.name]]}).execute())
        (sheet.values().update(spreadsheetId=self.sprade_sheet_id, range="Sheet1!D3", valueInputOption="USER_ENTERED", body={"values": [[docs.buyer_name.name]]}).execute())
        (sheet.values().update(spreadsheetId=self.sprade_sheet_id, range="Sheet1!E3", valueInputOption="USER_ENTERED", body={"values": [[docs.total_product_qty]]}).execute())
        # raise UserError((values))
        # return update