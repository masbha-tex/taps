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
    #pocode = fields.Char(related='picking_id.origin', string='PO', readonly=True)
    partner_name = fields.Char(string='Vendor', compute="_compute_partner_id", readonly=True, store=True)
    #quality_state = fields.Selection([
        #('none', 'To do'),
        #('pass', 'Passed'),
        #('fail', 'Failed')], string='Status', tracking=True,
        #default='none', copy=False)
    quality_state = fields.Selection(selection_add=[('deviation', 'Deviation'),('check', 'Checked by SC'),('informed', 'HOD Confirmation'),('confirm', 'Quality Head Approval'),('refuse', 'Refuse'),('fail',)])

    po_qty = fields.Float(compute='_compute_poqty', string='PO Qty', readonly=True)
    receive_qty = fields.Float(compute='_compute_reqty', string='Receive Qty', readonly=True)
    uom = fields.Many2one(related='product_id.uom_id', string='UOM', readonly=True)
    is_deviation = fields.Boolean("Is Deviation", readonly=True, store=True)
    receipt_date = fields.Datetime('Receipt Date', store=True, readonly=True)
    #product_id picking_id
    
    
    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('quality.check') or _('New')
        if 'point_id' in vals and not vals.get('test_type_id'):
            vals['test_type_id'] = self.env['quality.point'].browse(vals['point_id']).test_type_id.id
        
        data = self.env['stock.picking'].search([('id','=', vals.get('picking_id'))])
        vals['receipt_date'] = data.scheduled_date
        return super(QualityCheck, self).create(vals)
                        
    def write(self, vals):
        efefef = self.env['stock.picking'].search([('id','=', vals.get('picking_id'))])
        vals['receipt_date'] = efefef.scheduled_date
        return super(QualityCheck, self).write(vals)
    
    
    # def _compute_receipt_date(self):
    #     for rec in self:
    #         data = self.env['stock.picking'].search([('id','=', rec.picking_id.id)])
    #         rec.receipt_date = data.scheduled_date
    #         raise UserError((data.schedule_date))
            
    #def compute_po_qty(self):
        #for rec in self: 
            #data = self.env['purchase.order'].search([('name','=',rec.x_studio_source_po)])
            #rec.partner_name = data.partner_id.name
    
    #raise UserError(('fefefe'))
    # @api.depends('partner_name','po_qty','receive_qty')
    def _compute_partner_id(self):
        for rec in self:
            data = self.env['purchase.order'].search([('name','=',rec.x_studio_source_po)])
            rec.partner_name = data.partner_id.name
            
    def _compute_poqty(self):
        for rec in self:
            data = self.env['purchase.order'].search([('name','=',rec.x_studio_source_po)])
            dataline = self.env['purchase.order.line'].search([('order_id','=',data.id),('product_id','=',rec.product_id.id)])
            rec.po_qty = sum(dataline.mapped('product_qty'))
            
    def _compute_reqty(self):
        for rec in self:
            receive_line = self.env['stock.move.line'].search([('picking_id','=',rec.picking_id.id),('product_id','=',rec.product_id.id),('lot_id','=',rec.lot_id.id)])
            rec.receive_qty = sum(receive_line.mapped('product_uom_qty'))

    #raise_deviation check_deviation informed_deviation confirm_deviation
    
    def raise_deviation(self):
        self.write({'quality_state': 'deviation',
                    'user_id': self.env.user.id,
                    'control_date': datetime.now(),
                    'is_deviation': True
                   })
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

    def refuse_deviation(self):
        self.write({'quality_state': 'refuse',
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
    
    mode_company_id = fields.Many2one(related="check_id.company_id", string='Company', readonly=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    
    
    
    
