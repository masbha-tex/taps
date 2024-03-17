import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
import re
import math

class PackingError(models.TransientModel):
    _name = 'packing.error'
    _description = 'Packing Error'     
    # oa_ids_string =
    @api.model
    def get_operation_details(self):
        try:
            query = """
            SELECT 
                p.id,
                p.oa_id,
                p.actual_qty,
                p.done_qty,
                p.balance_qty,
                m.product_uom_qty,
                m.done_qty,
                m.balance_qty,
                m.state,
                (SELECT SUM(op.qty) FROM operation_details AS op WHERE op.next_operation='FG Packing' AND op.sale_order_line=p.sale_order_line) AS fg_done
            FROM 
                operation_packing AS p
                INNER JOIN manufacturing_order AS m ON p.sale_order_line=m.sale_order_line AND p.company_id=m.company_id AND p.oa_id=m.oa_id
            WHERE 
                m.company_id=1 AND p.balance_qty<>m.balance_qty AND m.oa_total_balance<0 AND m.state NOT IN ('closed','cancel');
            """
            self.env.cr.execute(query)
            operation_details = self.env.cr.fetchall()
            # Extracting oa_id values from the result set
            oa_ids = [record[1] for record in operation_details]  # Assuming oa_id is the second element in each tuple
            
            # Joining oa_id values with commas
            oa_ids_string = ','.join(str(oa_id) for oa_id in oa_ids)
            raise UserError((oa_ids_string))
            
            return oa_ids_string
            
            # return operation_details
        except Exception as e:
            raise exceptions.UserError(f"Error occurred while fetching operation details: {str(e)}")
        
                        