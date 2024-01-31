import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class CrmApprovalMatrix(models.Model):

    _name = 'crm.approval.matrix'
    _description = 'Crm Approval Matrix'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    


    model_name = fields.Char(string="Model Name")
    first_approval = fields.Many2many('res.users', string="First Approval" , relation='crm_approval_matrix_first_approval')
    second_approval = fields.Many2many('res.users', string="Second Approval", relation='crm_approval_matrix_second_approval')