# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from decimal import Decimal


class HrRetentionBonus(models.Model):
    _name = 'hr.retention.bonus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Retention Bonus Scheme"

    # @api.model
    # def default_get(self, field_list):
    #     result = super(HrRetentionBonus, self).default_get(field_list)
    #     if result.get('user_id'):
    #         ts_user_id = result['user_id']
    #     else:
    #         ts_user_id = self.env.context.get('user_id', self.env.user.id)
    #     result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
    #     return result

    def _compute_retention_bonus_amount(self):
        total_paid = 0.0
        for bonus in self:
            for line in bonus.bonus_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = bonus.bonus_amount - total_paid
            bonus.total_amount = bonus.bonus_amount
            bonus.balance_amount = balance_amount
            bonus.total_paid_amount = total_paid

    @api.depends('employee_id')
    def _compute_default_date(self):
        if self.employee_id:
            self.date = self.employee_id.joining_date
        else:
            fields.Date.today()
      
         

    name = fields.Char(string="Number", readonly=True, help="Name of the Retention Bonus Scheme")
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True, required=True, help="Employee")    
    date = fields.Date(string="Effective Date ", compute=_compute_default_date, store=True, required=True, readonly=False,  tracking=True, help="Effective Date") 
    duration = fields.Integer(default=1, string="Duration in Month", required=True, tracking=True, help="Duration in Month")
    

    
    @api.depends('date', 'duration')
    def _get_default_entitlement_date(self):
        for record in self:
            if record.date and record.duration:
                record.entitlement_date = record.date + relativedelta(months=record.duration)
                # record.payment_date = record.date + relativedelta(months=record.duration)
            else:
                record.entitlement_date = fields.Date.today()
                # record.payment_date = fields.Date.today()
    @api.depends('date', 'duration', 'entitlement_date')
    def _get_default_payment_date(self):
        for record in self:
            if record.date and record.duration and record.entitlement_date:
                record.payment_date = record.entitlement_date
                # record.payment_date = record.date + relativedelta(months=record.duration)
            else:
                record.payment_date = fields.Date.today()

    @api.depends('instant_payment')
    def _get_default_installment_date(self):
        for record in self:
            if record.instant_payment == '3':
                record.installment = 3
            elif record.instant_payment == '6':
                record.installment = 6
            elif record.instant_payment == '12':
                record.installment = 12
            else:
                record.installment = 1  

        
    entitlement_date = fields.Date(string="Entitlement Date", compute=_get_default_entitlement_date, store=True, required=True, readonly=False, help="Date of the Entitlement")   

    department_id = fields.Many2one('hr.department', related="employee_id.department_id", tracking=True, readonly=True, store=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", compute=_get_default_installment_date, help="Number of installments")
    # payment_date = fields.Date(string="Payment Start Date", required=True, tracking=True, default=fields.Date.today(), help="Date of the paymemt")
    payment_date = fields.Date(string="Payment Start Date", compute=_get_default_payment_date, store=True, required=True, tracking=True, readonly=False, help="Date of the paymemt")
    bonus_lines = fields.One2many('hr.retention.bonus.line', 'bonus_id', string="Bonus Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id", store=True, readonly=True, help="Company",
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True, required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.browse(55))
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", store=True, readonly=True, string="Job Position",
                                   help="Job position")
    bonus_amount = fields.Float(string="Bonus Amount",  tracking=True, required=True, help="Bonus amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_retention_bonus_amount',
                                help="Total Retention Bonus Scheme amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_retention_bonus_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", tracking=True, store=True, compute='_compute_retention_bonus_amount',
                                     help="Total paid amount")
    uid = fields.Many2one('res.users', string='HoD Approval', index=True, store=True, tracking=True) #, default=lambda self: self.env.user
    criteria = fields.Selection([
        ('Appointment Terms', 'Appointment Terms'),
        ('Special Retention Bonus', 'Special Retention Bonus'),
        ('GET policy', 'GET policy'),
        ('DET Policy', 'DET Policy'),
        ('ST policy', 'ST policy'),
        ('KMP policy', 'KMP policy'),
    ], string="Criteria", default='Appointment Terms', tracking=True, copy=True, required=True, readonly=False, store=True)
    instant_payment = fields.Selection([
        ('3', 'Payment by next 3 months'),
        ('6', 'Payment by next 6 months'),
        ('12', 'Payment by next 12 months'),
    ], string="Instant Payment", tracking=True, copy=True, store=True)        

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve0', 'HoD Approved'),
        ('approve1', 'HoHR Approved'),
        ('approve2', 'HoFC Approved'),
        ('approve3', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="Status", default='draft', tracking=True, store=True, required=True)
    
    submit_uid = fields.Many2one('res.users', ondelete="set null", string="Submit by", readonly=True, copy=True, store=True, help="Submit by")
    approve0_uid = fields.Many2one('res.users', ondelete="set null", string="HoD Approved", readonly=True, copy=True, store=True, help="HoD Approved")
    approve1_uid = fields.Many2one('res.users', ondelete="set null", string="HoHR Approved", readonly=True, copy=True, store=True, help="HoHR Approved")
    approve2_uid = fields.Many2one('res.users', ondelete="set null", string="HoFC Approved", readonly=True, copy=True, store=True, help="HoFC Approved")
    approve3_uid = fields.Many2one('res.users', ondelete="set null", string="DS Approved", readonly=True, copy=True, store=True, help="DS Approved")

    @api.model
    def create(self, values):
        loan_count = self.env['hr.retention.bonus'].sudo().search_count(
            [('employee_id', '=', values['employee_id']),
             ('balance_amount', '!=', 0)])#, ('state', '=', 'approve')
        count = self.env['hr.retention.bonus'].sudo().search_count(
            [('employee_id', '=', values['employee_id'])])#, ('state', '=', 'approve')        
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        if count:
            raise ValidationError(_("The employee has already a retention bonus record"))            
        else:
            retention_date = values.get('entitlement_date')
            values['name'] = self.env['ir.sequence'].next_by_code('hr.retention.bonus.seq', sequence_date=retention_date)
            res = super(HrRetentionBonus, self).create(values)
            if res.bonus_amount > 0:
                for reten in res:
                    reten.compute_installment()            
            return res

    def write(self, vals):
        res = super(HrRetentionBonus, self).write(vals)
        if vals.get('bonus_amount') or vals.get('payment_date') or vals.get('instant_payment'):
            for reten in self:
                reten.compute_installment()
        return res    
            
    # @api.onchange('bonus_amount', 'payment_date', 'installment')    
    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        if self.payment_date and self.bonus_amount > 0:
            for bonus in self:
                if bonus.bonus_lines:
                    bonus.bonus_lines.unlink()
                date_start = datetime.strptime(str(bonus.payment_date), '%Y-%m-%d')
                amount = bonus.bonus_amount / bonus.installment
                
                for i in range(1, bonus.installment + 1):
                    self.env['hr.retention.bonus.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': bonus.employee_id.id,
                        'bonus_id': bonus.id})
                    date_start = date_start + relativedelta(months=1)
                # raise UserError(('sss'))
                bonus._compute_retention_bonus_amount()
        else:
            if self.bonus_amount >= 0:
                for bonus in self:
                    if bonus.bonus_lines:
                        bonus.bonus_lines.unlink()
            
        # return True
        
    def action_draft(self):
        return self.write({'state': 'draft'})
        
    def action_refuse(self):
        self.write({'state': 'refuse'})
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_refused_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILTO')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Retention Bonus Refused',
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values).send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'refused',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }

    def action_submit(self):
        if self.uid:
            self.write({'state': 'submit', 'submit_uid': self.env.context.get('user_id', self.env.user.id)})
        else:
            raise UserError(('Maybe you forget to add HoD!!'))
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_submit_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILTO')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Retention Bonus for %s is waiting for HoD Approval' % self.employee_id.display_name,
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values)#.send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Submit Completed',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        
        
    
    def action_approval_0(self):
        self.write({'state': 'approve0', 'approve0_uid': self.uid})
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_approval_0_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'APPROVAL-1')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Retention Bonus for %s is waiting for HoHR Approval' % self.employee_id.display_name,
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values)#.send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'HoD Approved',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        # self.write({'state': 'approve0', 'approve0_uid': self.env.context.get('user_id', self.env.user.id)})
                
    def action_approval_1(self):
        self.write({'state': 'approve1', 'approve1_uid': self.env.context.get('user_id', self.env.user.id)})
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_approval_1_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'APPROVAL-2')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Retention Bonus for %s is waiting for HoFC Approval' % self.employee_id.display_name,
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values)#.send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'HoHR Approved',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        
    def action_approval_2(self):
        self.write({'state': 'approve2', 'approve2_uid': self.env.context.get('user_id', self.env.user.id)})  
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_approval_2_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'APPROVAL-3')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Retention Bonus for %s is waiting for CEO Approval' % self.employee_id.display_name,
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values)#.send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'HoFC Approved',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        
    def action_approval_3(self):
        self.write({'state': 'approve3', 'approve3_uid': self.env.context.get('user_id', self.env.user.id)})  
        template_submit = self.env.ref('hr_retention_bonus.mail_bonus_approval_3_template', raise_if_not_found=True)
        ctx = {
            'name': self.display_name,
            'employee_to_name': self.employee_id.display_name,
            'recipient_users': self.employee_id.user_id,
            'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', self.id),
        }
        _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)

        RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
        body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', self.ids, post_process=True)[self.id]
        body = f"{body}"
        # post the message
        matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILTO')], limit=1)
        if matrix:
            mailto = ','.join([email.email for email in matrix.next_user if email])
        matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
        if matrix_cc:
            mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
        if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': '%s "s Retention Bonus Approved' % self.employee_id.display_name,
                'body_html': body,
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
            else:
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values)#.send()
        else:
            raise UserError(('Maybe forget to add Email Matrix like..RE-MAILTO, RE-MAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Approved',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.bonus_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

                

    def unlink(self):
        for bonus in self:
            if bonus.state != 'draft':
                raise UserError(
                    'Once submitted, You cannot delete a Retention Bonus Scheme.')
        return super(HrRetentionBonus, self).unlink()

    def _action_retention_bonus_hr_reminder_email(self):
        docs = self.env['hr.retention.bonus'].search([('entitlement_date', '=', (date.today() + relativedelta(days=15)))])
        if docs:
            matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILTO')], limit=1)
            if matrix:
                mailto = ','.join([email.email for email in matrix.next_user if email])
            matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
            if matrix_cc:
                mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
            # if matrix or matrix_cc:
            mail_values = {
                'email_from': 'odoo@texzipperbd.com',
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': 'Upcoming Retention Bonus Entitlements',
                'body_html': 'Hello',
                'auto_delete': True,
                'email_to': mailto or '',
                'email_cc': mailcc or '',
            }
            try:
                template = self.env.ref('hr_retention_bonus.retention_bonus_hr_reminder_mail_template', raise_if_not_found=True)
                
            except ValueError:
                _logger.warning('QWeb template hr_retention_bonus.retention_bonus_hr_reminder_mail_template not found when sending Upcoming Retention Bonus Entitlements. Sending without layouting.')
            else:
    
                    
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb')
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)        
                
                # Create the mail
                self.env['mail.mail'].sudo().create(mail_values)

            


    def _action_retention_bonus_employee_reminder_email(self):
        # docs = self.env['hr.retention.bonus'].search([])
        # raise UserError((date.today()))
        docs = self.env['hr.retention.bonus'].search([('date', '<=', (date.today())),('entitlement_date','>=', date.today())])
        # docs.filtered(lambda re: (date.today()-re.date) isinstance(value, Decimal))
        
        for rec in docs:
            # current_date = date.today()
            # f_date = date.today() - relativedelta(years=3) - relativedelta(days=3)
            dif_year = date.today() - rec.date
            # total_seconds_difference = dif_year.total_seconds()
            # decimal_difference = total_seconds_difference / (3600 * 24)
            
            di_year = dif_year.days/365
            if not (isinstance(di_year, float) and di_year % 1 != 0):
                # raise UserError(('hudai'))
                template_submit = self.env.ref('hr_retention_bonus.retention_bonus_mail_template', raise_if_not_found=True)
                
                ctx = {
                    'name': rec.display_name,
                    'year' : round(di_year),
                    'employee_to_name': rec.employee_id.display_name,
                    'recipient_users': rec.employee_id.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.retention.bonus', rec.id),
                }
                _template_submit = template_submit._render(ctx, engine='ir.qweb', minimal_qcontext=True)
                
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)                
                body = RenderMixin._render_template(_template_submit, 'hr.retention.bonus', rec.ids, post_process=True)[rec.id]
                body = f"{body}"
                # raise UserError((body))
                matrix = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILTO')], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.retention.matrix'].sudo().search([('name', '=', 'RE-MAILCC')], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email])#+','+bonus.parent_id.email
                # if matrix or matrix_cc:
                mail_values = {
                    'email_from': 'odoo@texzipperbd.com',
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': '%s Retention Bonus Entitlements Anniversary' % rec.employee_id.display_name,
                    # 'subject': 'Retention Bonus Approved',
                    'body_html': body,
                    'auto_delete': True,
                    'email_to': rec.employee_id.email or '',
                    # 'email_to': mailto or '',
                    'email_cc': mailcc or '',
                }
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending retention bonus confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'])),
                    'model_description': self.env['ir.model']._get('hr.retention.bonus').display_name,
                    'company': self.env.company,
                    }
                    body = template._render(template_ctx, engine='ir.qweb')
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)        
                    
                    # Create the mail
                    self.env['mail.mail'].sudo().create(mail_values)



class InstallmentLine(models.Model):
    _name = "hr.retention.bonus.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    bonus_id = fields.Many2one('hr.retention.bonus', string="Retention Bonus Ref.", help="Retention Bonus Scheme")
    payment_date = fields.Date(string="Payment Start Date", related="bonus_id.payment_date", store=True)
    bonus_amount = fields.Float(string="Bonus Amount", related="bonus_id.bonus_amount", store=True)
    
    
    # adjustment_type = fields.Many2one('hr.payslip.input.type', string='Type',required=True,store=True, domain="[('code', '=', 'INCENTIVE')]", default=44)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_retention_bonus_scheme(self):
        """This compute the bonus amount and total retention scheme count of an employee.
            """
        self.retention_bonus_scheme_count = self.env['hr.retention.bonus'].sudo().search_count([('employee_id', '=', self.id)])

    retention_bonus_scheme_count = fields.Integer(string="Retention Bonus Scheme Count", compute='_compute_retention_bonus_scheme', groups="hr_retention_bonus.group_manager_retention_bonus,hr_retention_bonus.group_user_retention_bonus")
