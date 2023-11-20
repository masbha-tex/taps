from odoo import models, fields, api
import os
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
        # SCOPES=["https://googleapis.com/auth/spradesheets"]
        # SPRADESHEET_ID = "1xzHMo4HSMRAZ2k9D29meN4rUDMpgMgKPighGKoqsrAs"
        # Load credentials from the session.
        credentials = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            credentials = Credentials.from_authorized_user_file('token.json', self.scope)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
              credentials.refresh(Request())
            else:
              flow = InstalledAppFlow.from_client_secrets_file("src/user/google_sheet_connector/models/credentials.json",self.scope)
              credentials = flow.run_local_server(port=0)
    # Save the credentials for the next run
            with open("token.json", "w") as token:
              token.write(credentials.to_json())
        
        
        
        service = build("sheets", "v4", credentials=credentials)
           
            # Call the Sheets API
        sheet = service.spreadsheets()
        result = (sheet.values().get(spreadsheetId=self.sprade_sheet_id, range="Sheet1!A1:A1").execute())
        values = result.get("values", [])
        
        raise UserError((values))  

