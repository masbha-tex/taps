from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class PoApprovalDuration(models.Model):
    _name = "purchase.approval.duration"
    _auto = False
    _description = "Purchase Approval Duration"
    _check_company_auto = True
    
    po_id = fields.Many2one('purchase.order', string='PO' , store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company' , store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    
    create_order = fields.Date(string='PO Date', store=True)
    fun_a_date = fields.Date(string='Function Approval Date', store=True)
    scm_a_date = fields.Date(string='SCM Approval Date', store=True)
    fin_a_date = fields.Date(string='FINANCE Approval Date', store=True)
    full_a_date = fields.Date(string='FULLY Approval Date', store=True)
    
    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'purchase_approval_duration')
        query = """
        CREATE or REPLACE VIEW sale_order_rmc AS (
        select row_number() OVER() AS id ,sale_order_lines,oa_id,company_id,partner_id,buyer_name,payment_term,date_order,validity_date,product_id,product_template_id,fg_categ_type,product_uom,product_uom_qty,slidercodesfg,sizein,sizecm,sizemm,gap,dyedtape,ptopfinish,numberoftop,pbotomfinish,ppinboxfinish,dippingfinish,closing_date,currency_id,price_subtotal,rmc,percent from (
        select p.id as po_id,p.company_id,p.create_date,p.date_approved from purchase_order as p
        ) as a)"""
        self.env.cr.execute(query,(self.env.company.id,'a'))

    # @api.model
    # def _register_hook(self):
    #     # Create INSTEAD OF UPDATE trigger
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE FUNCTION instead_of_update_sale_order_rmc()
    #         RETURNS TRIGGER AS
    #         $$
    #         BEGIN
    #             -- Your logic to handle the update goes here
    #             -- You may need to update the underlying tables accordingly

    #             RETURN NEW;
    #         END;
    #         $$
    #         LANGUAGE plpgsql;
    #     """)

    #     self.env.cr.execute("""
    #         CREATE TRIGGER instead_of_update_sale_order_rmc
    #         INSTEAD OF UPDATE
    #         ON sale_order_rmc
    #         FOR EACH ROW
    #         EXECUTE FUNCTION instead_of_update_sale_order_rmc();
    #     """)
    #     super(SaleOrderRmc, self)._register_hook()