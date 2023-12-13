from odoo import models, fields, api


class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	idea_count = fields.Integer(compute='_compute_idea_count', store=False, string='Idea')
	
	def _compute_idea_count(self):
		Idea = self.env['hr.idea']
		self.idea_count = Idea.search_count([('employee_id','=',self.id)])