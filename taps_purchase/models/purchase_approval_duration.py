from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class PurchaseApprovalDuration(models.Model):
    _name = "purchase.approval.duration"
    _auto = False
    _description = "Purchase Approval Duration"
    _check_company_auto = True
    
    po_id = fields.Many2one('purchase.order', string='PO' , store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', related='po_id.partner_id', store=True, check_company=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, index=True, default=lambda self: self.env.company.id)#related='po_id.company_id', 
    # company_id = fields.Many2one('res.company', string='Company' ,related='po_id.company_id', store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    
    create_date = fields.Date(string='PO Date', store=True)
    fun_a_date = fields.Date(string='Function Approval Date', store=True)
    scm_a_date = fields.Date(string='SCM Approval Date', store=True)
    fin_a_date = fields.Date(string='FINANCE Approval Date', store=True)
    date_approved = fields.Date(string='FINAL Approval Date', store=True)
    amount_total = fields.Float(string='Total',store=True)
    duration_total = fields.Integer(string='Total Duration', compute='get_duration', readonly=True, store=True,  group_operator='avg')

    @api.onchange('create_date','fun_a_date','scm_a_date','fin_a_date','date_approved')
    def get_duration(self):
        for s in self:
            if s.create_date:
                if s.date_approved:
                    s.duration_total = (s.date_approved.date() - s.create_date.date()).days
                elif s.fin_a_date:
                    s.duration_total = (s.fin_a_date.date() - s.create_date.date()).days
                elif s.scm_a_date:
                    s.duration_total = (s.scm_a_date.date() - s.create_date.date()).days
                elif s.fun_a_date:
                    s.duration_total = (s.fun_a_date.date() - s.create_date.date()).days
            else:
                s.duration_total = 0
    
    

    def init(self):
    # Drop the existing view if it exists
        tools.drop_view_if_exists(self._cr, 'purchase_approval_duration')
        
        # Construct the query without the company filter date(date_order) - date(create_date)
        query = """
        CREATE OR REPLACE VIEW purchase_approval_duration AS (
        SELECT row_number() OVER() AS id, po_id,partner_id,company_id,
        create_date,fun_a_date,scm_a_date,fin_a_date,date_approved,amount_total,
        0 as duration_total
        FROM (
            SELECT
                p.id AS po_id,
                p.partner_id,
                p.company_id,
                p.create_date,
                (
                    SELECT date(ap.write_date)
                    FROM studio_approval_entry ap
                    WHERE ap.res_id = p.id
                        AND ap.model = 'purchase.order'
                        AND ap.rule_id = 13
                    LIMIT 1
                ) AS fun_a_date,
                (
                    SELECT date(ap.write_date)
                    FROM studio_approval_entry ap
                    WHERE ap.res_id = p.id
                        AND ap.model = 'purchase.order'
                        AND ap.rule_id = 14
                    LIMIT 1
                ) AS scm_a_date,
                (
                    SELECT date(ap.write_date)
                    FROM studio_approval_entry ap
                    WHERE ap.res_id = p.id
                        AND ap.model = 'purchase.order'
                        AND ap.rule_id = 16
                    LIMIT 1
                ) AS fin_a_date,
                date(p.date_approve) AS date_approved,
                p.amount_total
            FROM
                purchase_order p
        ) AS a)
        """
        self.env.cr.execute(query)

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