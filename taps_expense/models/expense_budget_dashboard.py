from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class ExpenseBudgetDashboard(models.Model):
    _name = "expense.budget.dashboard"
    _auto = False
    _description = "Expense Budget Dashboard"

    id = fields.Many2one('product.product',string='Code')
    default_code=fields.Char(string='Default Code')
    product_template= fields.Many2one('product.template', string='Sbd')
    name = fields.Char(string='Product Name')
    x_studio_super_expense_category = fields.Char(string='Super Expense Category Name')
    budget_year = fields.Char(string='Budget Year')
    budget_value = fields.Float(string='Budget Value')
    ytd = fields.Char(string='YTD')
    april = fields.Float(string='April')
    may = fields.Float(string='May')
    june = fields.Float(string='June')
    july = fields.Float(string='July')
    august = fields.Float(string='August')
    september = fields.Float(string='September')
    october = fields.Float(string='October')
    november = fields.Float(string='November')
    december = fields.Float(string='December')
    january = fields.Float(string='January')
    february = fields.Float(string='February')
    march = fields.Float(string='March')
    current_date = fields.Char(string='Current Month', compute='_compute_current_month')
    
    @api.depends()
    def _compute_current_month(self):
        for record in self:
            # Get the current month abbreviation (e.g., 'Aug' for August)
            current_date = fields.Date.context_today(self)
            month_abbreviation = current_date.strftime('%b')
            record.current_date = month_abbreviation
    # type = "EX_"

    def init(self):
        tools.drop_view_if_exists(self._cr, 'expense_budget_dashboard')
        
        query = """
        CREATE or REPLACE VIEW expense_budget_dashboard AS (
        SELECT  id,current_date,default_code, name,x_studio_super_expense_category,budget_value, budget_year, ytd, april,may,june,july,august,september,october,november,december,january,february,march
 FROM (
     SELECT a.name,
            b.id,
            b.default_code,
            b.x_studio_super_expense_category,
            (select sum(planned_amount) from crossovered_budget_lines z where b.id=z.product_id and z.crossovered_budget_state='validate') as budget_value,
            (select (DATE_PART('year',z.date_from)::TEXT) || '-' || (DATE_PART('year',z.date_to)::TEXT) as year from crossovered_budget_lines z where b.id=z.product_id and z.crossovered_budget_state='validate') as budget_year,
            
            '0' as ytd,
            
            (select sum(d.total_actual_amount) from hr_expense_sheet as d where d.product_id=b.id 
            and TO_CHAR(d.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-04-01'::TEXT
            and TO_CHAR(d.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-04-30'::TEXT) as april,
            (select sum(e.total_actual_amount) from hr_expense_sheet as e where e.product_id=b.id 
            and TO_CHAR(e.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-05-01'::TEXT
            and TO_CHAR(e.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-05-31'::TEXT) as may,
            (select sum(f.total_actual_amount) from hr_expense_sheet as f where f.product_id=b.id 
            and TO_CHAR(f.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-06-01'::TEXT
            and TO_CHAR(f.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-06-30'::TEXT) as june,
            (select sum(g.total_actual_amount) from hr_expense_sheet as g where g.product_id=b.id 
            and TO_CHAR(g.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-07-01'::TEXT
            and TO_CHAR(g.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-07-31'::TEXT) as july,
            (select sum(h.total_actual_amount) from hr_expense_sheet as h where h.product_id=b.id 
            and TO_CHAR(h.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-08-01'::TEXT
            and TO_CHAR(h.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-08-31'::TEXT) as august,
            (select sum(i.total_actual_amount) from hr_expense_sheet as i where i.product_id=b.id 
            and TO_CHAR(i.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-09-01'::TEXT
            and TO_CHAR(i.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-09-30'::TEXT) as september,
            (select sum(j.total_actual_amount) from hr_expense_sheet as j where j.product_id=b.id 
            and TO_CHAR(j.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-10-01'::TEXT
            and TO_CHAR(j.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-10-31'::TEXT) as october,
            (select sum(k.total_actual_amount) from hr_expense_sheet as k where k.product_id=b.id 
            and TO_CHAR(k.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-11-01'::TEXT
            and TO_CHAR(k.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-11-30'::TEXT) as november,
            (select sum(l.total_actual_amount) from hr_expense_sheet as l where l.product_id=b.id 
            and TO_CHAR(l.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2023-04-28')) || '-12-01'::TEXT
            and TO_CHAR(l.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2023-04-28')) || '-12-31'::TEXT) as december,
            (select sum(m.total_actual_amount) from hr_expense_sheet as m where m.product_id=b.id 
            and TO_CHAR(m.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2024-04-28')) || '-01-01'::TEXT
            and TO_CHAR(m.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2024-04-28')) || '-01-31'::TEXT) as january,
            (select sum(n.total_actual_amount) from hr_expense_sheet as n where n.product_id=b.id 
            and TO_CHAR(n.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2024-04-28')) || '-02-01'::TEXT
            and TO_CHAR(n.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2024-04-28')) || '-02-29'::TEXT) as february,
            (select sum(o.total_actual_amount) from hr_expense_sheet as o where o.product_id=b.id 
            and TO_CHAR(o.date_approve, 'YYYY-MM-DD') >= DATE_PART('year', date('2024-04-28')) || '-01-01'::TEXT
            and TO_CHAR(o.date_approve, 'YYYY-MM-DD') <= DATE_PART('year', date('2024-04-28')) || '-01-31'::TEXT) as march
            
            
     FROM product_template a
     INNER JOIN product_product b ON a.id = b.product_tmpl_id
     
     WHERE b.id in(select distinct product_id from hr_expense_sheet)
     AND b.id in(select distinct product_id from crossovered_budget_lines)
     
      
     group by a.name,b.id) as budget)
        """
        self.env.cr.execute(query)