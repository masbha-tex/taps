import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

class PackingError(models.TransientModel):
    _name = 'packing.error'
    _description = 'Packing Error' 
    
    oa_ids_string = fields.Char('OA IDs', readonly=True)  
    
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
                INNER JOIN manufacturing_order AS m ON p.sale_order_line=m.sale_order_line AND p.oa_id=m.oa_id
            WHERE 
                p.balance_qty<>m.balance_qty AND m.oa_total_balance<0 AND m.state NOT IN ('closed','cancel');
            """
            self.env.cr.execute(query)
            operation_details = self.env.cr.fetchall()

            # Extracting oa_id values from the result set
            oa_ids = [record[1] for record in operation_details]  # Assuming oa_id is the second element in each tuple
            
            # Joining oa_id values with commas
            self.oa_ids_string = ','.join(str(oa_id) for oa_id in oa_ids)
            
            return {'oa_ids_string': self.oa_ids_string}  # Return as a dictionary
            
        except Exception as e:
            logging.error("Error occurred while fetching operation details: %s", str(e))
            raise UserError("Error occurred while fetching operation details. Please check the logs for more information.")

    @api.model
    def solve(self):
        try:
            # oa_ids = [int(oa_id) for oa_id in self.oa_ids_string.split(',')]
            # oa_id_string = ','.join(str(oa_id) for oa_id in oa_ids)

            oa_id_string = self.oa_ids_string
            
            # Update operation_packing
            operation_packing_query = """
            UPDATE operation_packing
            SET done_qty = COALESCE((SELECT SUM(qty) FROM operation_details AS o WHERE o.oa_id = operation_packing.oa_id AND o.mrp_line = operation_packing.mrp_line AND o.next_operation='FG Packing'), 0)
            WHERE oa_id IN (%s);
            
            UPDATE operation_packing
            SET balance_qty = actual_qty - done_qty,
                ac_balance_qty = actual_qty - done_qty,
                state = CASE WHEN done_qty = actual_qty THEN 'done' ELSE 'waiting' END
            WHERE oa_id IN (%s);
            """ % (oa_id_string, oa_id_string)
            self.env.cr.execute(operation_packing_query)
            
            # Update manufacturing_order
            manufacturing_order_query = """
            UPDATE manufacturing_order
            SET done_qty = COALESCE((SELECT SUM(qty) FROM operation_details AS o WHERE o.oa_id = manufacturing_order.oa_id AND o.mrp_line = manufacturing_order.id AND o.next_operation='FG Packing'), 0)
            WHERE oa_id IN (%s);
            
            UPDATE manufacturing_order
            SET balance_qty = product_uom_qty - done_qty,
                state = CASE WHEN done_qty = product_uom_qty THEN 'done' ELSE 'waiting' END
            WHERE oa_id IN (%s);
            
            UPDATE manufacturing_order
            SET oa_total_balance = (SELECT AVG(a.oa_total_qty) - SUM(a.done_qty) FROM manufacturing_order AS a WHERE a.oa_id = manufacturing_order.oa_id)
            WHERE manufacturing_order.oa_id IN (%s);
            """ % (oa_id_string, oa_id_string, oa_id_string)
            self.env.cr.execute(manufacturing_order_query)
            
            # Commit the transaction
            self.env.cr.commit()
            
            return True
            
        except Exception as e:
            logging.error("Error occurred while solving packing error: %s", str(e))
            raise UserError("Error occurred while solving packing error. Please check the logs for more information.")
