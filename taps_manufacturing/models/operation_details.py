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
     

SIZE_BACK_ORDER_NUMERING = 3


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
        ('Assembly Output', 'Assembly Output'),
        ('Assembly Qc', 'Assembly Qc'),
        ('Plating', 'Plating'),
        ('Plating Output', 'Plating Output'),
        ('Painting', 'Painting'),
        ('Painting Output', 'Painting Output'),
        ('Slider Assembly', 'Slider Assembly'),
        ('Slider Assembly Output', 'Slider Assembly Output'),
        ('Packing', 'Packing'),
        ('Delivery', 'Delivery'),
        ('Issue', 'Issue'),
        ('Done', 'Done')],
        string='Next Operation', help="Next Operation")
    mr_req = fields.Many2one('stock.picking', 'Requisitions', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=True, compute='get_balance')
    uotput_qty = fields.Float(string='Output', default=0.0, readonly=False)
    pack_qty = fields.Integer(string='Pack Qty', default=0, readonly=False)
    fr_pcs_pack = fields.Integer(string='Remaining Qty', default=0, readonly=False, help='The remaining pcs to pack')
    fg_done_qty = fields.Integer(string='FG Done', default=0, readonly=False)
    fg_balance = fields.Integer(string='FG Balance', default=0, readonly=False, compute='get_balance')
    fg_output = fields.Integer(string='FG Output', default=0, readonly=False)
    cartoon_no = fields.Many2one('operation.details', string='Cartoon No', required=False, 
                                 domain="[('next_operation', '=', 'Delivery')]")
    
    num_of_lots = fields.Integer(string='N. of Lots', readonly=True, compute='get_lots')
    machine_no = fields.Many2one('machine.list', string='Machine No', required=False)
    capacity = fields.Integer(related='machine_no.capacity', string='Capacity', store=True)
    mrp_delivery = fields.Many2one('stock.picking', 'Delivery Order', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    total_weight = fields.Float(string='Total Weight', default=0.0, readonly=False)
    move_line = fields.Many2one('stock.move.line', 'Move Line Id', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('partial', 'Partial'),
        ('done', 'Done')],
        string='State')

    
    # lot_ids = fields.Many2one('operation.details', compute='get_lots', string='Lots', copy=False, store=True)
    
    def get_balance(self):
        for s in self:
            s.balance_qty = round((s.qty - s.done_qty),2)
            s.fg_balance = s.pack_qty - s.fg_done_qty
    
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
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_sizewiselot")
        #action["domain"] = [('default_id','=',self.mapped('id'))]
        return action

        # in_len = len(self)
        # i = 0
        # all_mrp_lines = ''
        # # raise UserError((in_len))
        # for op in self:
        #     if i == in_len-1:
        #         all_mrp_lines = all_mrp_lines + op.mrp_lines
        #     else:
        #         all_mrp_lines = all_mrp_lines + op.mrp_lines + ','
        #     i += 1
            
        # all_mrp_lines_st = str(all_mrp_lines)
        # mrp_ids = [int(id_str) for id_str in all_mrp_lines_st.split(',')]
        
        # action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_manufacturing_process_order")
        # # raise UserError((self.oa_id.ids))
        # # action['search_default_oa_id'] = self.oa_id

        # # action = self.env["ir.actions.actions"]._for_xml_id("stock.view_manufacturing_process_tree")
        # action['views'] = [
        #     (self.env.ref('taps_manufacturing.view_manufacturing_process_tree').id, 'tree'),
        # ]
        # # action['context'] = self.env.context
        # action['domain'] = [('id', 'in', mrp_ids),('oa_id', 'in', self.oa_id.ids)]
        # return action
    
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
                                            'finish':m_order.finish,
                                            'slidercodesfg':m_order.slidercodesfg,
                                            'top':m_order.ptopfinish,
                                            'bottom':m_order.pbotomfinish,
                                            'pinbox':m_order.ppinboxfinish,
                                            'sizein':m_order.sizein,
                                            'sizecm':m_order.sizecm,
                                            'operation_of':'lot',
                                            'work_center':3,
                                            'operation_by':'Metal chain making',
                                            'based_on':'size',
                                            'next_operation':'CM Output',
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

    def set_sizewiselot(self,active_model,ope_id,lot_line):
        operation = self.env["operation.details"].browse(ope_id)
        operation.update({'state':'done'})
        for l in lot_line:
            if l.quantity_string:
                # l = self.env["manufacturing.order"].browse(l.mrp_line)
                quantity_strings = l.quantity_string.split('+')
                for l_q in quantity_strings:
                    next = 'Assembly Output'
                    
                    if 'Metal' in l.mrp_line.fg_categ_type or 'AL' in l.mrp_line.fg_categ_type:
                        next = 'CM Output'
                    
                    ope = operation.create({'mrp_lines':l.mrp_line.id,
                                            'sale_lines':l.mrp_line.sale_order_line.id,
                                            'mrp_line':l.mrp_line.id,
                                            'sale_order_line':l.mrp_line.sale_order_line.id,
                                            'oa_id':l.mrp_line.oa_id.id,
                                            'buyer_name':l.mrp_line.buyer_name,
                                            'product_id':l.mrp_line.product_id.id,
                                            'product_template_id':l.mrp_line.product_template_id.id,
                                            'action_date':datetime.now(),
                                            'shade':l.mrp_line.shade,
                                            'finish':l.mrp_line.finish,
                                            'slidercodesfg':l.mrp_line.slidercodesfg,
                                            'top':l.mrp_line.ptopfinish,
                                            'bottom':l.mrp_line.pbotomfinish,
                                            'pinbox':l.mrp_line.ppinboxfinish,
                                            'sizein':l.mrp_line.sizein,
                                            'sizecm':l.mrp_line.sizecm,
                                            'operation_of':'lot',
                                            'work_center':operation[0].work_center.id,
                                            'operation_by':operation[0].work_center.name,
                                            'based_on':operation[0].based_on,
                                            'next_operation':next,
                                            'qty':l_q
                                            })

    def set_delivery_order(self,active_model,ope_id,delivery,delivery_line):
        operation = self.env["operation.details"].browse(ope_id)

        picking = self.env["stock.picking"].search([('origin','=',operation[0].oa_id.name),
                                                    ('state','not in',('draft','done','cancel'))])
        picking.update({'scheduled_date':delivery.deliveri_date})
        
        for l in operation:
            stock_move_line = self.env["stock.move.line"].search([('product_id','=',l.product_id.id),('reference','=',picking.name),('lot_id','=',l.move_line.lot_id.id)])
            stock_move_line.update({'qty_done':l.qty})

        operation.update({'state':'done','mrp_delivery':picking.id,'total_weight':delivery.total_weight})
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
            if self.qty <= vals.get('done_qty'):
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
            if operation == 'CM Output':
                up_date = m.update({'chain_making_done': m.chain_making_done + rest_qty})
                break
            if operation == 'Dipping Output':
                up_date = m.update({'diping_done': m.diping_done + rest_qty})
                break
            if operation == 'Assembly Output':
                up_date = m.update({'assembly_done': m.assembly_done + rest_qty})
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

        if operation.next_operation == 'Assembly Output':
            if operation.mrp_line:
                mrp_data = self.env["manufacturing.order"].browse(operation.mrp_line.id)
                mrp_update = mrp_data.update({'done_qty':mrp_data.done_qty + qty})
                
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',operation.oa_id.id)])
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':mrp_oa_data.oa_total_balance - qty})
                pr_pac_qty = mrp_data.product_template_id.pack_qty
                if pr_pac_qty:
                    pack_qty = math.ceil(qty/pr_pac_qty)
                    fraction_pc_of_pack = round(((qty/pr_pac_qty) % 1)*pr_pac_qty)

    

        if operation.next_operation in('Dyeing Output','CM Output','Dipping Output','Assembly Output','Plating Output','Painting Output','Slider Assembly Output'):
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
        if operation.next_operation == 'Dyeing Output':
            operation_of = 'input'

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

    # @api.onchange('done_qty')
    # def _done_qty(self):
    #     for s in self:
    #         if s.qty <= s.done_qty:
    #             s.state = 'done'
    #         elif s.done_qty == 0:
    #             s.state = 'waiting'
    #         else:
    #             s.state = 'partial'
    #         raise UserError(('eefe'))
    
    # @api.onchange('fg_output')
    # def _done_qty(self):
    #     for out in self:
    #         out.fg_done_qty = out.fg_done_qty + out.fg_output
            
    #         ope = self.env['operation.details'].create({'mrp_lines':out.mrp_lines,
    #                                                     'sale_lines':out.sale_lines,
    #                                                     'mrp_line':out.mrp_line.id,
    #                                                     'sale_order_line':out.sale_order_line.id,
    #                                                     'parent_id':out.id,
    #                                                     'oa_id':out.oa_id.id,
    #                                                     'buyer_name':out.buyer_name,
    #                                                     'product_template_id':out.product_template_id.id,
    #                                                     'action_date':datetime.now(),
    #                                                     'shade':out.shade,
    #                                                     'finish':out.finish,
    #                                                     'sizein':out.sizein,
    #                                                     'sizecm':out.sizecm,
    #                                                     'slidercodesfg':out.slidercodesfg,
    #                                                     'top':out.top,
    #                                                     'bottom':out.bottom,
    #                                                     'pinbox':out.pinbox,
    #                                                     'operation_of':'output',
    #                                                     # 'work_center':w_center,
    #                                                     'operation_by':out.work_center.name,
    #                                                     'based_on':'Packing',
    #                                                     'next_operation':'Delivery',
    #                                                     'qty':out.fg_output,
    #                                                     'pack_qty':out.pack_qty,
    #                                                     'fr_pcs_pack':fr_pcs_pack.fr_pcs_pack
    #                                                     })
    #         s.cartoon_no = ope.id
    #     return self

    # fg_done_qty
    # fg_output
    # cartoon_no
                
    # if s.qty <= s.done_qty:
    #     s.fg_done_qty = s.fg_done_qty + s.fg_output
    # elif s.done_qty == 0:
    #     s.state = 'waiting'
    # else:
    #     s.state = 'partial'
    # raise UserError(('eefe'))
            
    @api.onchange('uotput_qty')
    def _output(self):
        for out in self:
            pack_qty = 0
            fraction_pc_of_pack = 0
            pr_pac_qty = 0
            done_qty = out.done_qty + out.uotput_qty

            if out.balance_qty < out.uotput_qty:
                raise UserError(('You can not produce more then balance'))
            else:
                s = out.write({'done_qty':done_qty})#done_qty = done_qty
                manufac_ids = self.env["manufacturing.order"].browse(out.mrp_lines)
    
                # get_field = self.env["manufacturing.order"]._get_field('dyeing_plan_qty') #getattr(manufacturing_order, 'dyeing_plan_qty')
                # # set_field = getattr(taps_manufacturing.manufacturing_order, 'dyeing_output')
                # raise UserError((get_field))
                
    #'Assembly Output','Assembly Qc','Plating Output','Painting Output','Slider Assembly Output'
                #'Dyeing Output','Dyeing Qc','CM Output','Deeping Output','Deeping Qc'
                # out_qty = out.uotput_qty
                if out.next_operation in('Dyeing Output','CM Output','Dipping Output','Assembly Output','Plating Output','Painting Output','Slider Assembly Output'):
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
                if out.next_operation == 'Assembly Output':
                    mrp_data = self.env["manufacturing.order"].browse(out.mrp_line.id)
                    pr_pac_qty = mrp_data.product_template_id.pack_qty
                    if pr_pac_qty:
                        pack_qty = math.ceil(out.uotput_qty/pr_pac_qty)
                        fraction_pc_of_pack = round(((out.uotput_qty/pr_pac_qty) % 1)*pr_pac_qty)
                        
                    mrp_update = mrp_data.update({'done_qty':mrp_data.done_qty + out.uotput_qty, 'packing_done':fraction_pc_of_pack})
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
                if out.operation_of == 'qc':
                    operation_of = 'input'
                if out.next_operation == 'Dyeing Output':
                    operation_of = 'input'
                # operation = self.env["operation.details"].browse(self.id)
                # raise UserError((out.code,out.mrp_lines,out.mrp_line.id,out.sale_lines,out.sale_order_line.id))
                    
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
                                                            'qty':out.uotput_qty,
                                                            'pack_qty':pack_qty,
                                                            'fr_pcs_pack':fraction_pc_of_pack,
                                                            'capacity':pr_pac_qty,
                                                            'move_line':move_line
                                                            })
                out.uotput_qty = 0



