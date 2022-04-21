import ast
import json
from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR

class QualityCheck(models.Model):
    _inherit = "quality.check"
    quality_check_line = fields.One2many('quality.check.line', 'check_id', string='Order Lines', copy=True)
    product_category = fields.Many2one(related='product_id.categ_id', string='Product Category', readonly=True)
    
#     quality_state = fields.Selection([
#         ('none', 'To do'),
#         ('pass', 'Passed'),
#         ('fail', 'Failed')], string='Status', tracking=True,
#         default='none', copy=False)
    quality_state = fields.Selection(selection_add=[('deviation', 'Deviation'),('check', 'Checked by SC'),('informed', 'HOD Confirmation'),('confirm', 'Unit Head Approval'),('fail',)])
    

#     raise_deviation check_deviation informed_deviation confirm_deviation
    
    def raise_deviation(self):
        self.write({'quality_state': 'deviation',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        if self.env.context.get('no_redirect'):
            return True
        return self.redirect_after_pass_fail() 

    def check_deviation(self):
        self.write({'quality_state': 'check',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        if self.env.context.get('no_redirect'):
            return True
        return self.redirect_after_pass_fail()  
    
    def informed_deviation(self):
        self.write({'quality_state': 'informed',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        if self.env.context.get('no_redirect'):
            return True
        return self.redirect_after_pass_fail()      

    def confirm_deviation(self):
        self.write({'quality_state': 'confirm',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now()})
        if self.env.context.get('no_redirect'):
            return True
        return self.redirect_after_pass_fail()    
#    quality_category = fields.Selection([
#        ('n3_long_chain', 'N#3 Long Chain'),
#        ('n3_long_chain_grs', 'N#3 Long Chain Grs')], string='Quality Category', tracking=True,
#        default='n3_long_chain', copy=False)
   
    
    
    
class QualityCheckLine(models.Model):
    _name = 'quality.check.line'
    _description = 'Quality Check Details'
        
     
    
    
    
    @api.onchange('value1','value2','value3','value4','value5',
                 'value6','value7','value8','value9','value10','f_value','l_value')
    def set_status(self):
        for rec in self:
            if (rec.value1>=rec.f_value and rec.value1<=rec.l_value) and (rec.value2>=rec.f_value and rec.value2<=rec.l_value) and (rec.value3>=rec.f_value and rec.value3<=rec.l_value) and (rec.value4>=rec.f_value and rec.value4<=rec.l_value) and (rec.value5>=rec.f_value and rec.value5<=rec.l_value) and (rec.value6>=rec.f_value and rec.value6<=rec.l_value) and (rec.value7>=rec.f_value and rec.value7<=rec.l_value) and (rec.value8>=rec.f_value and rec.value8<=rec.l_value) and (rec.value9>=rec.f_value and rec.value9<=rec.l_value) and (rec.value10>=rec.f_value and rec.value10<=rec.l_value):
                rec.status = 'ok'
            else:
                rec.status = 'notok'
              
    
    

     
    #def _setParameterDomain(self):
    #    return [('product_category', '=', self.product_category.id)]
            
    
    name = fields.Char()
    check_id = fields.Many2one('quality.check', string='Check Reference', index=True, required=True, ondelete='cascade')
    parameter = fields.Many2one('quality.parameter', string="Parameter", domain="[('quality_category', '=', product_category)]",)
    product_category = fields.Many2one(related='check_id.product_category', string='Product Category', readonly=True)
    #company_id = fields.Many2one('res.company')
    #company_name = fields.Char(related='company_id.name')
    t_level = fields.Char(related='parameter.t_level')
    f_value = fields.Float(related='parameter.initial_value')
    l_value = fields.Float(related='parameter.last_value')
    value1 = fields.Float(string='V1')
    value2 = fields.Float(string='V2')
    value3 = fields.Float(string='V3')
    value4 = fields.Float(string='V4')
    value5 = fields.Float(string='V5')
    value6 = fields.Float(string='V6')
    value7 = fields.Float(string='V7')
    value8 = fields.Float(string='V8')
    value9 = fields.Float(string='V9')
    value10 = fields.Float(string='V10')
    status = fields.Selection([
        ('ok', 'Ok'),
        ('notok', 'Not Ok')], string='Status',
        copy=False, store = True, default='notok')
    
    
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    
    
    
    

