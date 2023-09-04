# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import _, api, fields, models, tools
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DF

class HrComplaint(models.Model):
	_name = "hr_complaint.complaint"
	_description = "Employee Complaint"
	_inherit = "mail.thread"
			
	name = fields.Char("Name")
	complaint_date = fields.Date("Date of Complaint", required=True, default=date.today())
	employee_id = fields.Many2one('hr.employee', "Employee", required=True)
	complaint_mode = fields.Selection([
            ('0', 'Telephone'),
            ('1', 'Other Verbal'),
            ('2', 'In writing')], "Method of Complaint", help="This is the mode by which the complaint was received.")
	complaint_type = fields.Selection([
            ('0', 'Formal'),
            ('1', 'Informal')], "Type of Complaint")
	complaint_source = fields.Selection([
            ('0', 'Client'),
            ('1', 'Public'),
	    ('2', 'Other Employee'),
	    ('3', 'Management')], "Source of Complaint")
	complaint_source_text = fields.Char('Complainant',size=100)
	complaint_outline = fields.Text('Outline of Complaint')
	complaint_evidence = fields.Text('Evidence')
	complaint_witnesses = fields.Text('Witnesses')
	recorded_by = fields.Many2one('hr.employee',"Complaint Recorded By",required=True)
	complaint_assessment = fields.Selection([
            ('0', 'Trivial'),
            ('1', 'Minor'),
	    ('2', 'Moderate'),
	    ('3', 'Serious'),
	    ('4', 'Very Serious')], "Seriousness of complaint")
#allegations questions
	stealing = fields.Boolean('Stealing')
	fraud = fields.Boolean('Fraud')
	violence = fields.Boolean('Threats and/or violence')
	safety = fields.Boolean('Safety breaches')
	discrimination = fields.Boolean('Discrimination')
#indicator question
	policy = fields.Boolean('Breach of contract/policy')
	client_contract = fields.Boolean('Breach of the company\'s contracts with clients')
	directions = fields.Boolean('Refusal to follow reasonable directions')
	performance = fields.Boolean('Unsatisfactory performance')
	behaviour = fields.Boolean('Inappropriate behaviour')
	property = fields.Boolean('Misuse of company property')
	evidence_sufficient = fields.Boolean('Is there sufficient evidence to investigate?')
	investigation_required =fields.Selection([
	    ('1', 'Yes - Formal'),
	    ('2', 'Yes - Informal'),
	    ('3', 'No')], 'Does the complaint require investigation?')
	complaint_refer = fields.Boolean('Does the complaint have to be referred to another organisation?')
	investigation_plan = fields.Text('Investigation methods/plan')
	assigned_to = fields.Many2one('hr.employee',"Investigator")
	assessor = fields.Many2one('hr.employee',"Assessor")
	assess_date = fields.Date('Assessment Completed')
	substantiated = fields.Boolean('Has the complaint been substantitated?')
	action_detail = fields.Text('Details')
	issues = fields.Text('Issues discovered')
	action_taken = fields.Selection([
	    ('1', 'Disciplinary Action'),
	    ('2', 'Formal Warning'),
	    ('3', 'Informal Warning'),
	    ('4', 'Record without warning'),
	    ('5', 'Remedial'),
	    ('6', 'No action')], 'Action to be taken', tracking=True)
	record_employee = fields.Boolean('Record on employee file', tracking=True)
	notes = fields.Text('Notes', tracking=True)
	completed_by = fields.Many2one('hr.employee','Completed By')
	state = fields.Selection([
            ('draft', 'New'),
            ('insufficient', 'Insufficient Evidence'),
            ('progress', 'Investigation in progress'),
            ('wait', 'Waiting for external investigation'),
            ('unsubstantiated','Unsubstantiated'),
            ('done', 'Done')], 'Status', required=True, tracking=True, default='draft')
	date_eta = fields.Date('To be completed')
	date_close = fields.Date('Date closed')
    
	@api.onchange('employee_id','complaint_date')
	def change_complaint(self):
		if self.employee_id:
			self.name = self.employee_id.name
		else:
			self.name = ''
		if self.complaint_date:
			self.name += ' (' + str(self.complaint_date) + ')'
			
	_order = 'complaint_date desc'

class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	complaint_count = fields.Integer(compute='_compute_ccount', store=False, string='Complaints')
	
	def _compute_ccount(self):
		Complaint = self.env['hr_complaint.complaint']
		self.complaint_count = Complaint.search_count([('employee_id','=',self.id)])
