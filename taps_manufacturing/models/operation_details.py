import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from werkzeug.urls import url_encode
from datetime import datetime
# from user.taps_manufacturing import manufacturing_order
     


class OperationDetails(models.Model):
    _name = "operation.details"
    _description = "Operation Details"
    _check_company_auto = True

    
    name = fields.Char(string='Code', store=True)
    mrp_lines = fields.Char(string='Mrp lines', store=True)
    sale_lines = fields.Char(string='Sale lines', store=True)
    
    mrp_line = fields.Many2one('manufacturing.order', string='Mrp Id', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    parent_id = fields.Many2one('operation.details', 'Parent Operation', index=True, ondelete='cascade')
    
    parent_ids = fields.Char(string='Parent Operations', store=True)
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    # buyer_name = fields.Char(string='Buyer', readonly=True)
    
    # product_id = fields.Many2one('product.product', 'Product', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True)
    # product_template_id = fields.Many2one('product.template', domain=[('sale_ok', '=', True)])


    product_id = fields.Many2one('product.product', check_company=True, string='Product Id')  # Unrequired company
    product_template_id = fields.Many2one('product.template', string='Product', related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)], store=True)
    
    fg_categ_type = fields.Selection(string='Item', related='product_template_id.fg_categ_type', store=True)
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_template_id.uom_id')
    
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    action_date = fields.Datetime(string='Action Date', readonly=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    
    slidercodesfg = fields.Char(string='Slider Code', store=True, readonly=True)
    finish = fields.Char(string='Finish', store=True, readonly=True)
    shade = fields.Char(string='Shade', store=True, readonly=True)
    shade_ref = fields.Char(string='Shade Ref.', store=True, readonly=True)
    sizein = fields.Char(string='Size (Inch)', store=True, readonly=True)
    sizecm = fields.Char(string='Size (CM)', store=True, readonly=True)
    
    top = fields.Char(string='Top', store=True, readonly=True)
    bottom = fields.Char(string='Bottom', store=True)
    pinbox = fields.Char(string='Pin-Box', store=True)
    
    operation_of = fields.Selection([
        ('plan', 'Planning'),
        ('lot', 'Create Lot'),
        ('output', 'Output'),
        ('qc', 'Quality Check'),
        ('input', 'Input'),
        ('req', 'Requisition')],
        string='Operation Of', help="What has done")
    work_center = fields.Many2one('mrp.workcenter', string='Assign To', store=True, readonly=True, help="Assign to")
    operation_by = fields.Char(string='Operation By', store=True, help="Done by")
    based_on = fields.Char(string='Based On', store=True)
    next_operation = fields.Selection([
        ('Planning', 'Planning'),
        ('Dyeing', 'Dyeing'),
        ('Dyeing Lot', 'Dyeing Lot'),
        ('Dyeing Output', 'Dyeing Output'),
        ('Dyeing Qc', 'Dyeing Qc'),
        ('Chain Making', 'Chain Making'),
        ('CM Lot', 'CM Lot'),
        ('CM Output', 'CM Output'),
        ('Dipping Output', 'Dipping Output'),
        ('Dipping Qc', 'Dipping Qc'),
        ('Assembly', 'Assembly'),
        ('Gapping', 'Gapping'),
        ('Assembly Output', 'Assembly Output'),
        ('Assembly Qc', 'Assembly Qc'),
        ('Plating', 'Plating'),
        ('Plating Output', 'Plating Output'),
        ('Painting', 'Painting'),
        ('Painting Output', 'Painting Output'),
        ('Slider Assembly', 'Slider Assembly'),
        ('Slider Assembly Output', 'Slider Assembly Output'),
        ('Packing Output', 'Packing Output'),
        ('FG Packing', 'FG Packing'),
        ('Delivery', 'Delivery'),
        ('Issue', 'Issue'),
        ('Done', 'Done')],
        string='Next Operation', help="Next Operation")
    mr_req = fields.Many2one('stock.picking', 'Requisitions', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    @api.depends('qty', 'done_qty')
    def get_balance(self):
        for s in self:
            if s.next_operation == 'Dyeing Qc':
                s.balance_qty = round((s.actual_qty - s.done_qty),2)
            else:
                s.balance_qty = round((s.qty - s.done_qty),2)
    
    @api.depends('pack_qty', 'fg_done_qty')        
    def get_fg_balance(self):
        for s in self:
            s.fg_balance = s.pack_qty - s.fg_done_qty
    
    @api.depends('qty', 'done_qty', 'actual_qty')
    def get_ac_balance(self):
        for s in self:
            if s.actual_qty>0:
                s.ac_balance_qty = round((s.actual_qty - s.done_qty),2)
    
    actual_qty = fields.Float(string='OA Tape Qty', readonly=True, store=True, group_operator="sum")
    ac_balance_qty = fields.Float(string='OA Tape Balance', readonly=False, store=True, compute='get_ac_balance', group_operator="sum")
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=False, store=True, compute='get_balance', group_operator="sum")
    uotput_qty = fields.Float(string='Output', default=0.0, readonly=False)
    pack_qty = fields.Integer(string='Pack Qty', readonly=False)
    fr_pcs_pack = fields.Integer(string='Remaining Qty', readonly=False, help='The remaining pcs to pack')
    fg_done_qty = fields.Integer(string='FG Done', default=0, readonly=False)
    fg_balance = fields.Integer(string='FG Balance', readonly=False, store=True, compute='get_fg_balance', group_operator="sum")
    fg_output = fields.Integer(string='FG Output', default=0, readonly=False, group_operator="sum")
    cartoon_no = fields.Many2one('operation.details', string='Cartoon No', required=False, 
                                 domain="[('next_operation', '=', 'Delivery')]")
    
    num_of_lots = fields.Integer(string='N. of Lots', readonly=True, compute='get_lots')
    machine_no = fields.Many2one('machine.list', string='Machine No', required=False)
    capacity = fields.Integer(related='machine_no.capacity', string='Capacity', store=True)
    mrp_delivery = fields.Many2one('stock.picking', 'Delivery Order', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    total_weight = fields.Float(string='Total Weight', default=0.0, readonly=False)
    move_line = fields.Many2one('stock.move.line', 'Move Line Id', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    plan_id = fields.Integer(string='Plan Id', store=True)
    plan_remarks = fields.Char(string='Plan Remarks', store=True)
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('partial', 'Partial'),
        ('done', 'Done'),
        ('hold', 'Hold')],
        string='State')
    revision_no = fields.Char(string='Revision No', store=True)
    
    # @api.model
    # def action_unplan(self):
    #     if self.state == 'waiting':
    #         self.state = 'waiting'
    
    # lot_ids = fields.Many2one('operation.details', compute='get_lots', string='Lots', copy=False, store=True)
    
    def unlink(self):
        mrp_ids = None
        mrp_id = []
        for order in self:
            production = None
            if (order.state == 'waiting') and (order.operation_by == 'Planning'):
                production = self.env["manufacturing.order"].search([('oa_id','=',order.oa_id.id),('shade','=',order.shade),('plan_ids','!=',False)])
                # if order.id not in(207,0):
                #     raise UserError((order.id,str(order.plan_id),str(production[0].plan_ids),order.oa_id.id,order.shade))
                production = production.filtered(lambda op: str(order.plan_id) in op.plan_ids)
                if production:
                    res_qty = order.qty
                    for p in production:
                        dn_qty = 0
                        if p.dyeing_plan_qty > 0:
                            if p.dyeing_plan_qty >= res_qty:
                                qty = p.dyeing_plan_qty - res_qty
                                dn_qty = res_qty
                            else:
                                qty = p.dyeing_plan_qty - p.dyeing_plan_qty
                                dn_qty = p.dyeing_plan_qty
                            if p.tape_con > 0.01 and qty <= 0.01:
                                qty = 0
                                
                            p.update({'dyeing_plan':None,'dyeing_plan_qty':qty,'dy_rec_plan_qty':None})
                            res_qty = res_qty - dn_qty
                            mrp_id.append(p.id)
                else:
                    raise UserError(('Something error, contact with admin'))
            else:
                raise UserError(('You can not delete this operation'))
        mrp_ids = ','.join([str(i) for i in sorted(mrp_id)])
        mrp_ids = [int(i) for i in sorted(mrp_ids.split(','))]
        mrp = self.env["manufacturing.order"].browse(mrp_ids)
        if mrp:
            mrp.update({'plan_ids':None})
        return super(OperationDetails, self).unlink()
        
    
    def _ids2str(self,field_name):
        field_data = getattr(self, field_name)
        if field_name == "ids":
            return ','.join([str(i) for i in sorted(field_data)])
        else:
            return ','.join([str(i.id) for i in sorted(field_data)])
    # def get_done_qty(self):
    #     for s in self:
    #         # operation_by Planning
    #         ch_operation = self.env['operation.details'].search([('parent_id', '=', s.id),('operation_of', '=', 'output')])
    #         s.done_qty = sum(ch_operation.mapped('uotput_qty'))
    
    def get_lots(self):
        for s in self:
            count_lots = self.env['operation.details'].search_count([('parent_id', '=', s.id),('operation_of', '=', 'lot')])
            s.num_of_lots = count_lots
            #s.lot_ids = count_lots.mapped('id')


            
    # @api.multi
    
            
        
    def button_requisition(self):
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_requisition")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        a = 'a'
        return action
    
    def button_delivery(self):
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_delivery")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        a = 'a'
        return action
    
    def button_group_output(self):
        for r in self:
            if r.next_operation not in ('Dyeing Output','Dyeing Qc'):
                raise UserError(('This is not for you'))
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_group_output")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action
        
    def button_output(self):
        self.ensure_one()
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_output")
        #action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action

    def button_createlot(self):
        self.ensure_one()
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_lot")
        #action["domain"] = [('default_id','=',self.mapped('id'))]
        return action
    
    def button_createmrplot(self):
        # self.ensure_one()
        self._check_company()
        oa_ids = self.mapped('oa_id')
        # oa_ids = ','.join([str(i) for i in sorted(self.oa_id.ids)])
        # raise UserError((len(oa_ids)))
        if len(oa_ids) > 1:
            raise UserError(('Create lot with single OA'))
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_sizewiselot")
        #action["domain"] = [('default_id','=',self.mapped('id'))]
        return action
    
    def set_requisition(self,company_id,active_model,ope_id,work_center,product_line):
        operation = self.env["operation.details"].search([])
        mrp_lines = sale_lines = parent_ids = oa_ids = None
        
        if active_model == 'manufacturing.order':
            # raise UserError(('sdfdfds'))
            m_order = self.env["manufacturing.order"].browse(ope_id)
            mrp_lines = ope_id
            sale_lines = ','.join([str(i) for i in sorted(m_order.sale_order_line.ids)])
            oa_ids = ','.join([str(i) for i in sorted(m_order.oa_id.ids)])
            sale_order = self.env["sale.order"].browse(oa_ids)
            oa_list = sale_order.mapped('name')
            #operation._ids2str('sale_order_line')
        else:
            operation = operation.browse(ope_id)
            parent_ids = operation._ids2str('ids')
            oa_ids = operation._ids2str('oa_id')
            sale_order = self.env["sale.order"].search([('id', 'in', (oa_ids,0))])#(oa_ids)
            oa_list = sale_order.mapped('name')

        # raise UserError((oa_list))
        pick = self.env["stock.picking"].create({'move_type':'direct',
                                                 'state':'draft',
                                                 'scheduled_date':datetime.now(),
                                                 'location_id':8,
                                                 'location_dest_id':15,
                                                 'picking_type_id':26,
                                                 'partner_id':self.env.user.partner_id.id,
                                                 'company_id':self.env.company.id,
                                                 'user_id':self.env.user.user_id,
                                                 'immediate_transfer':False,
                                                 'operation_lines':parent_ids,
                                                 'mrp_lines':mrp_lines,
                                                 'oa_ids': oa_ids,
                                                 'x_studio_oa_no':oa_list
                                                 })
        
        for prod in product_line:
            ope = operation.create({'mrp_lines':mrp_lines,
                                    'sale_lines':sale_lines,
                                    'parent_ids':parent_ids,
                                    'company_id':self.env.company.id,
                                    'action_date':datetime.now(),
                                    'operation_of':'req',
                                    'work_center':work_center,
                                    'operation_by':self.env.user.name,
                                    'product_id':prod.product_id.id,
                                    'based_on':'process',
                                    'next_operation':'Issue',
                                    'mr_req': pick.id,
                                    'qty':prod.product_qty
                                    })

            stockmove = self.env["stock.move"].create({'name':prod.product_id.product_tmpl_id.display_name,
                                                       'company_id':self.env.company.id,
                                                       'product_id':prod.product_id.id,
                                                       'description_picking':prod.product_id.product_tmpl_id.name,
                                                       # 'product_qty':prod.product_qty,
                                                       'product_uom_qty':prod.product_qty,
                                                       'product_uom':prod.product_id.product_tmpl_id.uom_id.id,
                                                       'location_id':8,
                                                       'location_dest_id':15,
                                                       'partner_id':self.env.user.partner_id.id,
                                                       'picking_id':pick.id,
                                                       'state':'draft',
                                                       'procure_method':'make_to_stock',
                                                       'picking_type_id':26,
                                                       'reference':pick.name
                                                       })
            
    
    def set_lot(self,active_model,ope_id,lot_line):
        if lot_line:
            if active_model == 'manufacturing.order':
                operation = self.env["operation.details"].browse(1)
                m_order = self.env["manufacturing.order"].browse(ope_id)
                #numberoftop  
                for l in lot_line:
                    ope = operation.create({'mrp_lines':ope_id,
                                            'sale_lines':m_order.sale_order_line.id,
                                            'mrp_line':ope_id,
                                            'sale_order_line':m_order.sale_order_line.id,
                                            'oa_id':m_order.oa_id.id,
                                            'buyer_name':m_order.buyer_name,
                                            'product_id':m_order.product_id.id,
                                            'product_template_id':m_order.product_template_id.id,
                                            'action_date':datetime.now(),
                                            'shade':m_order.shade,
                                            'shade_ref':m_order.shade_ref,
                                            'finish':m_order.finish,
                                            'slidercodesfg':m_order.slidercodesfg,
                                            'top':m_order.ptopfinish,
                                            'bottom':m_order.pbotomfinish,
                                            'pinbox':m_order.ppinboxfinish,
                                            'sizein':m_order.sizein,
                                            'sizecm':m_order.sizecm,
                                            'operation_of':'lot',
                                            'work_center':17,
                                            'operation_by':'Metal chain making',
                                            'based_on':'size',
                                            'next_operation':'Dipping Output',
                                            'qty':l.material_qty
                                            })
                    
            else:
                operation = self.env["operation.details"].browse(ope_id)
                for l in lot_line:
                    ope = operation.create({'mrp_lines':operation.mrp_lines,
                                            'sale_lines':operation.sale_lines,
                                            'mrp_line':operation.mrp_line,
                                            'sale_order_line':operation.sale_order_line,
                                            'parent_id':ope_id,
                                            'oa_id':operation.oa_id.id,
                                            'buyer_name':operation.buyer_name,
                                            'product_id':operation.product_id.id,
                                            'product_template_id':operation.product_template_id.id,
                                            'action_date':datetime.now(),
                                            'shade':operation.shade,
                                            'shade_ref':operation.shade_ref,
                                            'finish':operation.finish,
                                            'slidercodesfg':operation.slidercodesfg,
                                            'top':operation.top,
                                            'bottom':operation.bottom,
                                            'pinbox':operation.pinbox,
                                            'sizein':operation.sizein,
                                            'sizecm':operation.sizecm,
                                            'operation_of':'lot',
                                            'work_center':operation.work_center.id,
                                            'operation_by':operation.work_center.name,
                                            'based_on':operation.based_on,
                                            'next_operation':next,
                                            'qty':l.material_qty
                                            })

    def set_sizewiselot(self,active_model,ope_id,tape_qty,lot_line):
        operation = self.env["operation.details"].browse(ope_id)
        rs_q = tape_qty
        
        for op in operation:
            qty = 0
            # raise UserError((op.qty,rs_q))
            if op.qty > rs_q:
                qty = rs_q
            else:
                qty = op.qty
            if op.qty == qty:
                op.update({'done_qty':op.done_qty + qty,'state':'done'})
            else:
                op.update({'done_qty':op.done_qty + qty,'state':'partial'})
                
            rs_q = rs_q - qty
            # raise UserError((rs_q))
            if rs_q == 0:
                break
        for l in lot_line:
            if l.size_total>0:
                # l = self.env["manufacturing.order"].browse(l.mrp_line)
                # quantity_strings = l.quantity_string.split('+')
                l_capa = 4000
                if l.lot_capacity > 0:
                    l_capa = l.lot_capacity
                lots = 0
                if l.lots>0:
                    lots = l.lots
                else:
                    lots = math.ceil(l.size_total/l_capa)
                rest_q = l.size_total
                m_orders = None
                m_lines =  [int(id_str) for id_str in l.mrp_line.split(',')]
                
                m_orders = self.env["manufacturing.order"].browse(m_lines)
                for l_q in range(lots):
                    if rest_q > l_capa:
                        qty = l_capa
                    else:
                        qty = rest_q
                    # raise UserError((m_orders[0].fg_categ_type))
                    next = 'Assembly Output'
                    work_center = operation[0].work_center.id
                    if 'Metal' in m_orders[0].fg_categ_type or 'AL' in m_orders[0].fg_categ_type:
                        next = 'Dipping Output'
                        work_center = 17
                    # 'mrp_line':l.mrp_line.id,
                    # 'sale_order_line':l.mrp_line.sale_order_line.id,
                    # for mr_li in l.mrp_line:
                   
                    ope = operation.create({'mrp_lines':l.mrp_line,
                                            'sale_lines':l.sale_lines,
                                            'oa_id':m_orders[0].oa_id.id,
                                            'buyer_name':m_orders[0].buyer_name,
                                            'product_id':m_orders[0].product_id.id,
                                            'product_template_id':m_orders[0].product_template_id.id,
                                            'action_date':datetime.now(),
                                            'shade':m_orders[0].shade,
                                            'shade_ref':m_orders[0].shade_ref,
                                            'finish':m_orders[0].finish,
                                            'slidercodesfg':m_orders[0].slidercodesfg,
                                            'top':m_orders[0].ptopfinish,
                                            'bottom':m_orders[0].pbotomfinish,
                                            'pinbox':m_orders[0].ppinboxfinish,
                                            'sizein':m_orders[0].sizein,
                                            'sizecm':m_orders[0].sizecm,
                                            'operation_of':'lot',
                                            'work_center':work_center,
                                            'operation_by':operation[0].work_center.name,
                                            'based_on':operation[0].based_on,
                                            'next_operation':next,
                                            'qty':qty
                                            })
                    rest_q = rest_q - l_capa

    def set_delivery_order(self,active_model,ope_id,delivery,delivery_line):
        operation = self.env["operation.details"].browse(ope_id)

        picking = self.env["stock.picking"].search([('origin','=',operation[0].oa_id.name),
                                                    ('state','not in',('draft','done','cancel'))])
        picking.update({'scheduled_date':delivery.deliveri_date})
        
        for l in operation:
            stock_move_line = self.env["stock.move.line"].search([('product_id','=',l.product_id.id),('reference','=',picking.name),('lot_id','=',l.move_line.lot_id.id)])
            stock_move_line.update({'qty_done':l.qty})

        operation.update({'state':'done','mrp_delivery':picking.id,'total_weight':delivery.total_weight})
        if picking:
            # raise UserError(('grrgr'))
            picking.sudo().button_validate()
                    
                    
    def action_view_lots(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        
        result = self.env["ir.actions.actions"]._for_xml_id('taps_manufacturing.action_operation_details')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'parent_id': self.id, 'operation_of': 'lot'}
        lots_ = self.env['operation.details'].search([('parent_id', '=', self.id),('operation_of', '=', 'lot')])
        lot_ids = lots_.mapped('id')
        #raise UserError((lot_ids))
        # choose the view_mode accordingly
        result['domain'] = "[('id','in',%s)]" % (lot_ids)
        return result

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        seq_date = None
        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.now()))

        if vals.get('operation_of') == "lot":
            ref = self.env['ir.sequence'].next_by_code('mrp.lot', sequence_date=seq_date)
            vals['name'] = ref
        if vals.get('next_operation') == "Delivery":
            if 'name' in vals:
                if vals.get('name'):
                    vals['name'] = vals.get('name')
                else:
                    ref = self.env['ir.sequence'].next_by_code('fg.cartoon', sequence_date=seq_date)
                    vals['name'] = ref
        vals['state'] = 'waiting'
        result = super(OperationDetails, self).create(vals)
        return result                

    # @api.model
    def write(self, vals):
        if 'done_qty' in vals:
            if self.next_operation == 'Dyeing Qc':
                if round(self.actual_qty,2) <= round(vals.get('done_qty'),2):
                    vals['state'] = 'done'
                elif vals.get('done_qty') == 0:
                    vals['state'] = 'waiting'
                else:
                    vals['state'] = 'partial'
            else:
                if round(self.qty,2) <= round(vals.get('done_qty'),2):
                    vals['state'] = 'done'
                elif vals.get('done_qty') == 0:
                    vals['state'] = 'waiting'
                else:
                    vals['state'] = 'partial'
        if 'fg_output' in vals:
            if self.fg_balance < vals.get('fg_output'):
                raise UserError(('You can not pack more then balance'))
            else:
                fg_done = self.fg_done_qty +  vals.get('fg_output')
                vals['fg_done_qty'] = fg_done
                ret_qty = 0
                qty = 0
                capacity = self.product_template_id.pack_qty
                if self.pack_qty == fg_done:
                    vals['state'] = 'done'
                    ret_qty = self.fr_pcs_pack
                    qty = ((vals.get('fg_output') * capacity) - capacity) + ret_qty
                else:
                    vals['state'] = 'partial'
                    qty = vals.get('fg_output') * capacity
                name = None
                if 'cartoon_no' in vals:
                    # cartoon = vals.get('cartoon_no')
                    out = self.env['operation.details'].search([('id', '=', vals.get('cartoon_no'))])
                    #self.env['operation.details'].filtered(lambda op: op.id == 120)
                    #.sorted(key=lambda pr: pr.id)[:1]
                    if out:
                        name = out.name
                #     out.update({'qty': out.qty + vals.get('fg_output')})
                # else:
                # raise UserError((qty,vals.get('fg_output')))
                ope = self.env['operation.details'].create({'name':name,
                                                            'mrp_lines':self.mrp_lines,
                                                            'sale_lines':self.sale_lines,
                                                            'mrp_line':self.mrp_line.id,
                                                            'sale_order_line':self.sale_order_line.id,
                                                            'parent_id':self.id,
                                                            'oa_id':self.oa_id.id,
                                                            'buyer_name':self.buyer_name,
                                                            'product_id':self.product_id.id,
                                                            'product_template_id':self.product_template_id.id,
                                                            'action_date':datetime.now(),
                                                            'shade':self.shade,
                                                            'shade_ref':self.shade_ref,
                                                            'finish':self.finish,
                                                            'sizein':self.sizein,
                                                            'sizecm':self.sizecm,
                                                            'slidercodesfg':self.slidercodesfg,
                                                            'top':self.top,
                                                            'bottom':self.bottom,
                                                            'pinbox':self.pinbox,
                                                            'operation_of':'output',
                                                            # 'work_center':w_center,
                                                            'operation_by':self.work_center.name,
                                                            'based_on':'Packing',
                                                            'next_operation':'Delivery',
                                                            'qty':qty,
                                                            'pack_qty':vals.get('fg_output'),
                                                            'fr_pcs_pack':ret_qty,
                                                            'move_line':self.move_line.id
                                                            })
                vals['fg_output'] = 0
                if name:
                    a = ''
                else:
                    vals['cartoon_no'] = ope.id
        # raise UserError((vals.get('state')))
        result = super(OperationDetails, self).write(vals)
        return result                


    def set_mrp_output(self,operation,mrplines,qty,material):
        # oa_ids = ','.join([str(i) for i in sorted(mrplines)])
        mrp_ids = [int(id_str) for id_str in mrplines.split(',')]
        
        # raise UserError((mrp_ids))
        mrp_data = self.env["manufacturing.order"].browse(mrp_ids)
        # 'Dyeing Qc','CM Output','Dipping Qc','Assembly Qc','Plating Output','Painting Output','Slider Assembly Output'

        rest_qty = qty
        for m in mrp_data:
            if operation == 'Dyeing Output':
                if m.dyeing_plan_qty > 0:
                    up_date = m.update({'dyeing_output': m.dyeing_output + rest_qty})
                    break
            if operation == 'Dyeing Qc':
                if m.dyeing_plan_qty > 0:
                    up_date = m.update({'dyeing_qc_pass': m.dyeing_qc_pass + rest_qty})
                    break
            if operation == 'CM Output':
                up_date = m.update({'chain_making_done': m.chain_making_done + rest_qty})
                break
            if operation == 'Dipping Output':
                up_date = m.update({'diping_done': m.diping_done + rest_qty})
                break
            if operation == 'Assembly Output':
                up_date = m.update({'assembly_done': m.assembly_done + rest_qty})
                break
            if operation == 'Packing Output':
                up_date = m.update({'packing_done': m.packing_done + rest_qty})
                break
            if operation in ('Plating Output','Painting Output'):
                
                if material == 'slider':
                    if m.plating_plan_qty > 0:
                        up_date = m.update({'plating_output': m.plating_output + rest_qty})
                    break
                    
                if material == 'top':
                    if m.top_plat_plan_qty > 0:
                        up_date = m.update({'top_plat_output': m.top_plat_output + rest_qty})
                    break
                    
                if material == 'bottom':
                    if m.bot_plat_plan_qty > 0:
                        up_date = m.update({'bot_plat_output': m.bot_plat_output + rest_qty})
                    break
                    
                if material == 'pinbox':
                    if m.pin_plat_plan_qty > 0:
                        up_date = m.update({'pin_plat_output': m.pin_plat_output + rest_qty})
                    break
                    
            if operation == 'Slider Assembly Output':
                if m.sli_asmbl_plan_qty > 0:
                    up_date = m.update({'sli_asmbl_output': m.sli_asmbl_output + rest_qty})
                    break
            

           # dyeing_output plating_output top_plat_output bot_plat_output pin_plat_output sli_asmbl_output chain_making_done diping_done assembly_done packing_done         
    def set_group_output(self,mo_ids,qty):
        # raise UserError(('Under Construction'))
        operation = self.env["operation.details"].browse(mo_ids)
        qty_ = round((qty/len(operation)),2)
        # 'Dyeing Qc'
        # raise UserError((qty))
        if operation[0].next_operation == 'Dyeing Qc':
            rest_qty = qty
            while rest_qty > 0:
                for op in operation:
                    o_qty = op.uotput_qty + rest_qty
                    if op.ac_balance_qty >= o_qty:
                        op.write({'uotput_qty': op.uotput_qty + o_qty})
                        op._output()
                        rest_qty = 0
                    else:
                        if op.ac_balance_qty > op.uotput_qty:
                            o_qty = op.ac_balance_qty - op.uotput_qty
                            if o_qty > 0:
                                op.write({'uotput_qty':op.uotput_qty + o_qty})
                                rest_qty = rest_qty - o_qty
                                op._output()
                            else:
                                rest_qty = 0
        else:
            for op in operation:
                op.write({'uotput_qty':qty_})
                op._output()


    
    def set_output(self,output_model,mo_ids,manuf_date,qty,output_of):
        # raise UserError((self,output_model,mo_ids,manuf_date,qty,output_of))
        
        pack_qty = 0
        fraction_pc_of_pack = 0
        operation = self.env["operation.details"].browse(mo_ids)
        dqt = operation.done_qty + qty
        ope = operation.write({'action_date':manuf_date,'done_qty':dqt})
        
        if operation.parent_id:
            parent_id = operation.parent_id
            while (parent_id):
                if mo_ids != parent_id.id:
                    operation_p = self.env["operation.details"].browse(parent_id.id)
                    dqt = operation_p.done_qty + qty
                    ope = operation_p.write({'done_qty':dqt})
                parent_id = parent_id.parent_id

        if operation.next_operation == 'Packing Output':
            if operation.mrp_line:
                mrp_data = self.env["manufacturing.order"].browse(operation.mrp_line.id)
                mrp_update = mrp_data.update({'done_qty':mrp_data.done_qty + qty})
                
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',operation.oa_id.id)])
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':mrp_oa_data.oa_total_balance - qty})
                pr_pac_qty = mrp_data.product_template_id.pack_qty
                if pr_pac_qty:
                    pack_qty = math.ceil(qty/pr_pac_qty)
                    fraction_pc_of_pack = round(((qty/pr_pac_qty) % 1)*pr_pac_qty)

    

        if operation.next_operation in('Dyeing Output','Dyeing Qc','CM Output','Dipping Output','Assembly Output','Packing Output','Plating Output','Painting Output','Slider Assembly Output'):
           up = self.set_mrp_output(operation.next_operation,operation.mrp_lines,qty,operation.based_on)
            
        next = None
        w_center = operation.work_center.id
        if operation.next_operation in('Slider Assembly Output','Painting Output','Plating Output'):
            next = 'Assembly'
            
        process_flow = self.env["process.sequence"].search([]) #('item','=',self.fg_categ_type.name)
        # cur_process = process_flow.filtered(lambda pr: pr.item == operation.fg_categ_type and pr.process == operation.next_operation)
        cur_process = process_flow.filtered(lambda pr: pr.item == operation.fg_categ_type and pr.process == operation.next_operation)

        
        if cur_process:
            next_process = process_flow.filtered(lambda pr: pr.item == operation.fg_categ_type and pr.sequence > cur_process.sequence).sorted(key=lambda pr: pr.sequence)[:1]
            
            if next_process:
                next = next_process.process
                w_center = next_process.work_center.id
            else:
                next = 'Done'

        operation_of = 'output'
        if operation.operation_of == 'qc':
            operation_of = 'input'
        # if operation.next_operation == 'Dyeing Output':
        #     operation_of = 'input'

        # raise UserError((w_center,operation.work_center.name,pack_qty,fraction_pc_of_pack))
        ope = self.env['operation.details'].create({'name':operation.name,
                                                    'mrp_lines':operation.mrp_lines,
                                                    'sale_lines':operation.sale_lines,
                                                    'mrp_line':operation.mrp_line.id,
                                                    'sale_order_line':operation.sale_order_line.id,
                                                    'parent_id':operation.id,
                                                    'oa_id':operation.oa_id.id,
                                                    'buyer_name':operation.buyer_name,
                                                    'product_id':operation.product_id.id,
                                                    'product_template_id':operation.product_template_id.id,
                                                    'action_date':datetime.now(),
                                                    'shade':operation.shade,
                                                    'shade_ref':operation.shade_ref,
                                                    'finish':operation.finish,
                                                    'sizein':operation.sizein,
                                                    'sizecm':operation.sizecm,
                                                    'slidercodesfg':operation.slidercodesfg,
                                                    'top':operation.top,
                                                    'bottom':operation.bottom,
                                                    'pinbox':operation.pinbox,
                                                    'operation_of':operation_of,
                                                    'work_center': w_center,
                                                    'operation_by':operation.work_center.name,
                                                    'based_on':'Lot Code',
                                                    'next_operation':next,
                                                    'qty':qty,
                                                    'pack_qty':pack_qty,
                                                    'fr_pcs_pack':fraction_pc_of_pack
                                                    })
        
            
    @api.onchange('uotput_qty')
    def _output(self):
        for out in self:
            pack_qty = 0
            fraction_pc_of_pack = 0
            pr_pac_qty = 0
            done_qty = out.done_qty + out.uotput_qty

            # if out.balance_qty < out.uotput_qty:
            #     raise UserError(('You can not produce more then balance'))
            # else:
            s = out.write({'done_qty':done_qty})#done_qty = done_qty
            manufac_ids = self.env["manufacturing.order"].browse(out.mrp_lines)

            # get_field = self.env["manufacturing.order"]._get_field('dyeing_plan_qty') #getattr(manufacturing_order, 'dyeing_plan_qty')
            # # set_field = getattr(taps_manufacturing.manufacturing_order, 'dyeing_output')
            # raise UserError((get_field))
            
#'Assembly Output','Assembly Qc','Plating Output','Painting Output','Slider Assembly Output'
            #'Dyeing Output','Dyeing Qc','CM Output','Deeping Output','Deeping Qc'
            # out_qty = out.uotput_qty
            if out.next_operation in('Dyeing Output','Dyeing Qc','CM Output','Dipping Output','Assembly Output','Packing Output','Plating Output','Painting Output','Slider Assembly Output'):
                up = self.set_mrp_output(out.next_operation,out.mrp_lines,out.uotput_qty,out.based_on)
            
            if out.parent_id:
                parent_id = out.parent_id
                while (parent_id):
                    if out.parent_id != parent_id.id:
                        operation_p = self.env["operation.details"].browse(parent_id.id)
                        dqt = operation_p.done_qty + out.uotput_qty
                        ope = operation_p.write({'done_qty':dqt})
                    parent_id = parent_id.parent_id
    
            move_line = None
            if out.next_operation == 'Packing Output':
                # mrp_ids = [int(i) for i in sorted(mrp_ids.split(','))]
                mrp_lines = [int(id_str) for id_str in out.mrp_lines.split(',')]
                mrp_data = self.env["manufacturing.order"].browse(mrp_lines)
                pr_pac_qty = mrp_data[0].product_template_id.pack_qty
                mrp_lines = None
                if pr_pac_qty:
                    pack_qty = math.ceil(out.uotput_qty/pr_pac_qty)
                    fraction_pc_of_pack = round(((out.uotput_qty/pr_pac_qty) % 1)*pr_pac_qty)

                if mrp_data:
                    out_qty = out.uotput_qty / len(mrp_data)
                    # fr_sum = out.uotput_qty - int(out_qty)*len(mrp_update)
                    # extra = fr_sum
                    each_qty = out_qty
                    while each_qty > 0:
                        for datas in mrp_data:
                            outqty = 0
                            if datas.balance_qty > out_qty:
                                outqty = out_qty
                            else:
                                outqty = datas.balance_qty
                            # extra += out_qty - outqty
                            mrp_update = datas.update({'done_qty':datas.done_qty + outqty})
                            # , 'packing_done':fraction_pc_of_pack
                            each_qty = each_qty - outqty
                        
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',out.oa_id.id)])
                tot_b =  sum(mrp_oa_data.mapped('oa_total_balance'))/ len(mrp_oa_data) # mrp_oa_data.oa_total_balance - out.uotput_qty
                tot_b = tot_b - out.uotput_qty
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':tot_b})
# id,name,sequence,company_id,product_id,product_qty,product_uom_qty,product_uom,location_id,location_dest_id,state,origin,procure_method,scrapped,group_id,propagate_cancel,picking_type_id,warehouse_id,additional,reference,is_done,production_id,unit_factor,weight                   
                
                stockmove = self.env["stock.move"].create({'name':'New',
                                                           'sequence':10,
                                                           'company_id':self.env.company.id,
                                                           'product_id':out.product_id.id,
                                                           # 'product_qty':out.uotput_qty,
                                                           'product_uom_qty':out.uotput_qty,
                                                           'product_uom':out.product_id.product_tmpl_id.uom_id.id,
                                                           'location_id':15,
                                                           'location_dest_id':8,
                                                           'state':'done',
                                                           'procure_method':'make_to_stock',
                                                           'scrapped':False,
                                                           # 'group_id':11129,
                                                           'propagate_cancel':False,
                                                           'picking_type_id':8,
                                                           'warehouse_id':1,
                                                           'additional':False,
                                                           # 'reference':,
                                                           'is_done':True,
                                                           # 'production_id':,
                                                           'unit_factor':out.uotput_qty
                                                           # 'weight':,
                                                           # 'reference':pick.name
                                                           })
                # raise UserError(('trtrtr'))
                lot_producing_id = self.env['stock.production.lot'].create({
                    'product_id': out.product_id.id,
                    'company_id': self.env.company.id
                })
              
                stockmove_line = self.env["stock.move.line"].create({'move_id': stockmove.id,
                                                                     'company_id':self.env.company.id,
                                                                     'product_id':out.product_id.id,
                                                                     'product_uom_id':out.product_id.product_tmpl_id.uom_id.id,
                                                                     # 'product_qty':out.uotput_qty,
                                                                     # 'product_uom_qty':out.uotput_qty,
                                                                     'qty_done':out.uotput_qty,
                                                                     'lot_id':lot_producing_id.id,
                                                                     'date':datetime.now(),
                                                                     'location_id':15,
                                                                     'location_dest_id':8,
                                                                     'state':'done',# 'reference':,
                                                                     'qty_onhand':out.uotput_qty
                                                                     })
                move_line = stockmove_line.id

                picking = self.env["stock.picking"].search([('origin','=',out.oa_id.name),('state','not in',('draft','done','cancel'))])
                if picking:
                    picking.action_assign()
                
            next = None
            w_center = out.work_center.id
            if out.next_operation in('Slider Assembly Output','Painting Output','Plating Output'):
                next = 'Assembly'
                
            process_flow = self.env["process.sequence"].search([]) #('item','=',self.fg_categ_type.name)
            cur_process = process_flow.filtered(lambda pr: pr.item == out.fg_categ_type and pr.process == out.next_operation)
            if cur_process:
                next_process = process_flow.filtered(lambda pr: pr.item == out.fg_categ_type and pr.sequence > cur_process.sequence).sorted(key=lambda pr: pr.sequence)[:1]
                if next_process:
                    next = next_process.process
                    w_center = next_process.work_center.id
                else:
                    next = 'Done'
            
            operation_of = 'output'
            actual_qty = out.actual_qty
            if out.operation_of == 'qc':
                operation_of = 'input'
            
            existing_qc = None
            if out.next_operation == 'Dyeing Output':
                operation_of = 'qc'
                # mrp_lines = [int(id_str) for id_str in out.mrp_lines.split(',')]
                # mrp_data = self.env["manufacturing.order"].browse(mrp_lines)
                # mrp_data = mrp_data.filtered(lambda pr: pr.shade == out.shade and pr.oa_id.id == out.oa_id.id)
                # actual_qty = sum(mrp_data.mapped('tape_con'))
                tape_in_qc = self.env["operation.details"].search([('plan_id','=', out.plan_id)])
                oa_ids = tape_in_qc.mapped('oa_id')
                # oa_ids = ','.join([str(i) for i in sorted(oa_ids)])
                # oa_ids = [int(i) for i in sorted(oa_ids.split(','))]
                rest_qty = out.uotput_qty
                while rest_qty > 0:
                    excessqty = 0
                    for i, oa in enumerate(sorted(oa_ids)):
                        # ('mrp_lines','=', out.mrp_lines),
                        existing_qc = self.env["operation.details"].search([('oa_id','=', oa.id),('shade','=', out.shade),('next_operation','=', 'Dyeing Qc')])
                        # tape_in_qc.filtered(lambda dy: dy.oa_id.id == oa.id and dy.shade == out.shade and dy.next_operation == 'Dyeing Qc')
                        qc_qty = 0
                
                        if existing_qc:
                            qc_qty = existing_qc.qty + rest_qty
                            if existing_qc.actual_qty >= qc_qty:
                                qc_update = existing_qc.update({'qty':qc_qty})
                                rest_qty = rest_qty - rest_qty
                                excessqty = 0
                            else:
                                if existing_qc.actual_qty > existing_qc.qty:
                                    qc_qty = existing_qc.actual_qty - existing_qc.qty
                                    if qc_qty > 0:
                                        qc_update = existing_qc.update({'qty':existing_qc.qty + qc_qty})
                                    rest_qty = rest_qty - qc_qty
                                    # raise UserError((rest_qty))
                                if i+1 == len(oa_ids):
                                    excessqty = rest_qty
                                # qc_qty = qc_qty - existing_qc.qty
                                # # qc_qty = rest_qty -  
                                # # if rest_qty < existing_qc.actual_qty:
                                # #     qc_update = existing_qc.update({'qty': existing_qc.actual_qty})
                                # qc_update = existing_qc.update({'qty': qc_qty})
                                # rest_qty = 0 #rest_qty - existing_qc.actual_qty
                                
                        else:
                            # mrp_lines = [int(id_str) for id_str in out.mrp_lines.split(',')]
                            mrp_data = self.env["manufacturing.order"].search([('oa_id','=',oa.id),('shade','=',out.shade)])
                            # mrp_data = mrp_data.filtered(lambda pr: pr.shade == out.shade and pr.oa_id.id == out.oa_id.id)
                            actual_qty = sum(mrp_data.mapped('tape_con'))
                            a = ''
                            if actual_qty >= rest_qty:
                                qc_qty = rest_qty
                                rest_qty = rest_qty - qc_qty
                            else:
                                qc_qty = actual_qty
                                rest_qty = rest_qty - qc_qty

                            
                            ope = self.env['operation.details'].create({'name':out.name,
                                                                        'mrp_lines':out.mrp_lines,
                                                                        'sale_lines':out.sale_lines,
                                                                        'mrp_line':out.mrp_line.id,
                                                                        'sale_order_line':out.sale_order_line.id,
                                                                        'parent_id':out.id,
                                                                        'oa_id':oa.id,
                                                                        'buyer_name':out.buyer_name,
                                                                        'product_id':out.product_id.id,
                                                                        'product_template_id':out.product_template_id.id,
                                                                        'action_date':datetime.now(),
                                                                        'shade':out.shade,
                                                                        'shade_ref':out.shade_ref,
                                                                        'finish':out.finish,
                                                                        'sizein':out.sizein,
                                                                        'sizecm':out.sizecm,
                                                                        'slidercodesfg':out.slidercodesfg,
                                                                        'top':out.top,
                                                                        'bottom':out.bottom,
                                                                        'pinbox':out.pinbox,
                                                                        'operation_of':operation_of,
                                                                        'work_center':w_center,
                                                                        'operation_by':out.work_center.name,
                                                                        'based_on':'Lot Code',
                                                                        'next_operation':next,
                                                                        'actual_qty':actual_qty,
                                                                        'qty':qc_qty,
                                                                        'pack_qty':pack_qty,
                                                                        'fr_pcs_pack':fraction_pc_of_pack,
                                                                        'capacity':pr_pac_qty,
                                                                        'move_line':move_line
                                                                        })
                        # raise UserError((rest_qty))
                        if rest_qty == 0:
                            break
                    #i+1 == len(oa_ids)
                    if excessqty > 0:
                        excessqty = round((excessqty/len(oa_ids)),2)
                        rest_qty = 0
                        # raise UserError((excessqty,len(oa_ids)))
                        existing_qc = None
                        for l in sorted(oa_ids):
                            existing_qc = self.env["operation.details"].search([('oa_id','=', l.id),('shade','=', out.shade),('next_operation','=', 'Dyeing Qc')])
                            qc_update = existing_qc.update({'qty': existing_qc.qty + excessqty})
                            # raise UserError((existing_qc.qty + excessqty))

            
            else:
                ope = self.env['operation.details'].create({'name':out.name,
                                                            'mrp_lines':out.mrp_lines,
                                                            'sale_lines':out.sale_lines,
                                                            'mrp_line':out.mrp_line.id,
                                                            'sale_order_line':out.sale_order_line.id,
                                                            'parent_id':out.id,
                                                            'oa_id':out.oa_id.id,
                                                            'buyer_name':out.buyer_name,
                                                            'product_id':out.product_id.id,
                                                            'product_template_id':out.product_template_id.id,
                                                            'action_date':datetime.now(),
                                                            'shade':out.shade,
                                                            'shade_ref':out.shade_ref,
                                                            'finish':out.finish,
                                                            'sizein':out.sizein,
                                                            'sizecm':out.sizecm,
                                                            'slidercodesfg':out.slidercodesfg,
                                                            'top':out.top,
                                                            'bottom':out.bottom,
                                                            'pinbox':out.pinbox,
                                                            'operation_of':operation_of,
                                                            'work_center':w_center,
                                                            'operation_by':out.work_center.name,
                                                            'based_on':'Lot Code',
                                                            'next_operation':next,
                                                            'actual_qty':actual_qty,
                                                            'qty':out.uotput_qty,
                                                            'pack_qty':pack_qty,
                                                            'fr_pcs_pack':fraction_pc_of_pack,
                                                            'capacity':pr_pac_qty,
                                                            'move_line':move_line
                                                            })
            out.uotput_qty = 0



