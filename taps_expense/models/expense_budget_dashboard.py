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
    # product_template= fields.Many2one('product.template', string='Sbd')
    name = fields.Char(string='Product Name')
    x_studio_super_expense_category = fields.Char(string='Super Expense Category Name')
    budget_year = fields.Char(string='Budget Year')
    budget_value = fields.Float(string='Budget Value')
    monthly_budget = fields.Float(string='Monthly Budget')
    ytd = fields.Float(string='YTD')
    ytd_avg = fields.Float(string='YTD AVG')
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
        fromdate = datetime.now().replace(month=4).replace(day=1).date()
        todate = datetime.now().replace(month=3).replace(day=31).date()
        fromyear = toyear = datetime.now().year
        if datetime.now().month < 4:
            fromyear = datetime.now().year - 1
            fromdate = fromdate.replace(year=fromyear)
        else:
            toyear = datetime.now().year + 1
            todate = todate.replace(year=toyear)
        
        

        query = """
        CREATE or REPLACE VIEW expense_budget_dashboard AS (
        SELECT  id, current_date,default_code, name,x_studio_super_expense_category,budget_value,(budget_value/12) as monthly_budget, budget_year, ytd,(ytd/6) as ytd_avg, april,may,june,july,august,september,october,november,december,january,february,march
 FROM (
     SELECT a.name,b.id,b.default_code,b.x_studio_super_expense_category,
     (select sum(planned_amount) from crossovered_budget_lines z where b.id=z.product_id and z.crossovered_budget_state='validate') as budget_value,
     concat(%s,'-',%s) as budget_year,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date(d.date_approve)>=date(%s) and date(d.date_approve)<=date(%s)) as ytd,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 4) as april,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 5) as may,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 6) as june,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 7) as july,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 8) as august,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 9) as september,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 10) as october,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 11) as november,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 12) as december,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 1) as january,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 2) as february,
     (select sum(d.total_actual_amount*(select case when d.ex_currency_id=2 then cr.rate else 1 end from res_currency_rate as cr where cr.currency_id=55 and cr.company_id=d.company_id and cr.name<=d.date_approve order by cr.id desc limit 1)) from hr_expense_sheet as d where d.product_id=b.id and
     date_part('year',d.date_approve) = %s and date_part('month',d.date_approve) = 3) as march
     FROM product_template a
     INNER JOIN product_product b ON a.id = b.product_tmpl_id
     WHERE b.id in(select distinct product_id from hr_expense_sheet)
     AND b.id in(select distinct product_id from crossovered_budget_lines)
     group by a.name,b.id) as budget)
        """
        self.env.cr.execute(query,(fromyear,toyear,fromdate,todate,fromyear,fromyear,fromyear,fromyear,fromyear,fromyear,fromyear,fromyear,fromyear,toyear,toyear,toyear))