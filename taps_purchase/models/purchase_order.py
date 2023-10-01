from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount


class ApprovalEntry(models.Model):
    _inherit = 'studio.approval.entry'
    
    @api.model
    def create(self, vals):
        model_name = self.env['studio.approval.rule'].search([('id','=',vals['rule_id'])]).model_name
        if model_name == 'purchase.order':
            user_ = self.env['res.users'].search([('id','=',vals['user_id'])])
            po = self.env['purchase.order'].search([('id', '=', vals['res_id'])]).write({'last_approver':vals['user_id'],'x_studio_last_confirmation':user_.display_name})
        
        entry = super().create(vals)
        return entry


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    #record.write({'x_studio_last_confirmation': record.last_approver.display_name})
    
    last_approver = fields.Many2one(
        string="Last Approver",
        comodel_name="res.users",
        store=True
    )
    is_received = fields.Boolean(string="Receive Status", related='is_shipped', store=True)
    po_type = fields.Selection([('Import', 'Import'), ('Local', 'Local')], 'PO Type',required=True, states={'cancel': [('readonly', True)], 'done': [('readonly', True)], 'purchase': [('readonly', True)], 'to approve': [('readonly', True)]})
    
    
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
        
        vals, partner_vals = self._write_partner_values(vals)
        vals['last_approver'] = None
        vals['x_studio_last_confirmation'] = None
        res = super(PurchaseOrder, self_comp).create(vals)
        if partner_vals:
            res.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return res
    
    
    def action_send_card(self,id):
        template = self.env['mail.template'].browse(19)
        template.send_mail(id, force_send=True)

        
    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        self.check_access_rights('read')
        povalue = 0

        result = {
            'all_to_send': 0,
            'all_waiting': 0,
            'all_late': 0,
            'my_to_send': 0,
            'my_waiting': 0,
            'my_late': 0,
            'all_avg_order_value': 0,
            'all_avg_days_to_purchase': 0,
            'all_total_last_7_days': 0,
            'all_sent_rfqs': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }

        one_week_ago = fields.Datetime.to_string(fields.Datetime.now().replace(day=1))# - relativedelta(days=7)
        # This query is brittle since it depends on the label values of a selection field
        # not changing, but we don't have a direct time tracker of when a state changes
        query = """SELECT SUM(RawPOvalue) FROM(SELECT SUM(CASE WHEN po.date_approve >= %s THEN COALESCE(po.amount_total / NULLIF(po.currency_rate, 0), po.amount_total) ELSE 0 END) as RawPOvalue
                   FROM purchase_order po
                   JOIN res_company comp ON (po.company_id = comp.id)
                   WHERE po.state in ('purchase', 'done') AND po.itemtype='spares'
                     AND po.company_id in %s
                     UNION
                     select 0 as RawPOvalue) as a
                """

        companies_ids =  self._context.get('allowed_company_ids')
        #self.env['res.company'].browse(self._context.get('allowed_company_ids')).ids
        # companies = ','.join([str(i) for i in sorted(companies_ids.ids)])
        self._cr.execute(query, [one_week_ago, tuple(companies_ids)] )
        res = self.env.cr.fetchone()
        currency = self.env.company.currency_id
        #result['all_sent_rfqs'] = res[0] or 0
        povalues = round(res[0] or 0, 2)
        result['all_sent_rfqs'] = format_amount(self.env, povalues, currency)
        # easy counts
        po = self.env['purchase.order']
        result['all_to_send'] = po.search_count([('state', '=', 'draft')])
        result['my_to_send'] = po.search_count([('state', '=', 'draft'), ('user_id', '=', self.env.uid)])
        result['all_waiting'] = po.search_count([('state', '=', 'sent'), ('date_order', '>=', fields.Datetime.now())])
        result['my_waiting'] = po.search_count([('state', '=', 'sent'), ('date_order', '>=', fields.Datetime.now()), ('user_id', '=', self.env.uid)])
        result['all_late'] = po.search_count([('state', 'in', ['draft', 'sent', 'to approve']), ('date_order', '<', fields.Datetime.now())])
        result['my_late'] = po.search_count([('state', 'in', ['draft', 'sent', 'to approve']), ('date_order', '<', fields.Datetime.now()), ('user_id', '=', self.env.uid)])

        # Calculated values ('avg order value', 'avg days to purchase', and 'total last 7 days') note that 'avg order value' and
        # 'total last 7 days' takes into account exchange rate and current company's currency's precision. Min of currency precision
        # is taken to easily extract it from query.
        # This is done via SQL for scalability reasons
        # AVG(COALESCE(po.amount_total / NULLIF(po.currency_rate, 0), po.amount_total)),
        #(select sum(planned_amount) from crossovered_budget_lines where date_part('month',date_from)=date_part('month',CURRENT_DATE) and itemtype='spares' and company_id=po.company_id) SpareBudget,
        #and itemtype='raw' 
        query = """SELECT SUM(RawBudget),SUM(SpareBudget),SUM(RawPOvalue) FROM (SELECT (select sum(planned_amount) from crossovered_budget_lines where date_part('month',date_from)=date_part('month',CURRENT_DATE) and date_part('year',date_from)=date_part('year',CURRENT_DATE) and company_id=po.company_id) RawBudget,0 as SpareBudget,
                          SUM(CASE WHEN date(po.date_approve) >= date(%s) THEN COALESCE(po.amount_total / NULLIF(po.currency_rate, 0), po.amount_total) ELSE 0 END) RawPOvalue
                   FROM purchase_order po
                   JOIN res_company comp ON (po.company_id = comp.id)
                   WHERE po.state in ('purchase', 'done') AND po.itemtype='raw'
                     AND po.company_id in %s group by po.company_id
                     Union
                     select 0 as RawBudget,0 as SpareBudget,0 as RawPOvalue
                     ) as a
                """
        
        self._cr.execute(query, [one_week_ago, tuple(companies_ids)])
        res = self.env.cr.fetchone()
        currency = self.env.company.currency_id
        povalue = round(res[2] or 0, 2)
        #povalues + round(res[2] or 0, 2)
        budgetalue = round(res[0] or 0, 2)
        if povalue*budgetalue==0:
            percent=0
        else:
            percent = round((povalue/budgetalue)*100,2)
        result['all_avg_order_value'] = format_amount(self.env, budgetalue, currency)
        result['all_avg_days_to_purchase'] = percent
        #format_amount(self.env, res[1] or 0, currency)
        result['all_total_last_7_days'] = format_amount(self.env, povalue, currency)

        return result


class PurchaseOrderLineInherit(models.Model):
    _inherit = "purchase.order.line"

    quality_standard = fields.Char(string="Quality Standaed")
    last_purchase_price = fields.Char(string="Last Purchase",compute="_last_purchase_price")
    
    
    def _last_purchase_price(self):
        for line in self:
            domain = [
                
                ("product_id", "=", line.product_id.id),
                ("order_id.date_approve", "<", line.order_id.create_date),
                ("order_id.state", "=", "purchase"),
            ]
            docs = self.env["purchase.order.line"].search(domain, limit=1)
            line.last_purchase_price = str("{:.2f}".format(docs.price_unit))+" "
            if docs.order_id.currency_id.name:
                line.last_purchase_price += str(docs.order_id.currency_id.name)
            line.last_purchase_price += " ," +str(docs.order_id.name)
            # raise UserError((docs.id))
    
    
