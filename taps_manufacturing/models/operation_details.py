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

    code = fields.Char(string='Lot Code', store=True)
    mrp_lines = fields.Char(string='Mrp lines', store=True)
    sale_lines = fields.Char(string='Sale lines', store=True)
    
    mrp_line = fields.Many2one('manufacturing.order', string='Mrp Id', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    parent_id = fields.Many2one('operation.details', 'Parent Operation', index=True, ondelete='cascade')
    
    parent_ids = fields.Char(string='Parent Operations', store=True)
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True)
    product_template_id = fields.Many2one('product.template', domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Selection(string='Item', related='product_template_id.fg_categ_type')
    
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
        ('Deeping Output', 'Deeping Output'),
        ('Deeping Qc', 'Deeping Qc'),
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
        ('Issue', 'Issue'),
        ('Done', 'Done')],
        string='Next Operation', help="Next Operation")
    mr_req = fields.Many2one('stock.picking', 'Requisitions', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=True, compute='get_balance')
    uotput_qty = fields.Float(string='Output', default=0.0, readonly=False)
    num_of_lots = fields.Integer(string='N. of Lots', readonly=True, compute='get_lots')
    # lot_ids = fields.Many2one('operation.details', compute='get_lots', string='Lots', copy=False, store=True)
    
    def get_balance(self):
        for s in self:
            s.balance_qty = s.qty - s.done_qty
    
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
        
    def set_requisition(self,company_id,active_model,ope_id,work_center,product_line):
        
        operation = self.env["operation.details"].search([])
        mrp_lines = sale_lines = parent_ids = oa_ids = None
        
        if active_model == 'manufacturing.order':
            raise UserError(('sdfdfds'))
            m_order = self.env["manufacturing.order"].browse(ope_id)
            mrp_lines = ope_id
            sale_lines = ','.join([str(i) for i in sorted(m_order.sale_order_line.ids)])
            oa_ids = ','.join([str(i) for i in sorted(m_order.oa_id.ids)])
            #operation._ids2str('sale_order_line')
        else:
            operation = operation.browse(ope_id)
            parent_ids = operation._ids2str('ids')
            oa_ids = operation._ids2str('oa_id')

        #raise UserError((self.env.company.id,))    
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
                                                 'oa_ids': oa_ids
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
            vals['code'] = ref
        
        result = super(OperationDetails, self).create(vals)
        return result                
    

    def set_output(self,output_model,mo_ids,manuf_date,qty,output_of):
        
        operation = self.env["operation.details"].browse(mo_ids)
        ope = operation.update({'action_date':manuf_date,'done_qty':operation.done_qty + qty})
        
        if operation.parent_id:
            parent_id = operation.parent_id
            while (parent_id):
                if mo_ids != parent_id.id:
                    operation_p = self.env["operation.details"].browse(parent_id.id)
                    ope = operation_p.update({'done_qty':operation_p.done_qty + qty})
                parent_id = parent_id.parent_id

        if operation.next_operation == 'Assembly Qc':
            if operation.mrp_line:
                mrp_data = self.env["manufacturing.order"].browse(operation.mrp_line.id)
                mrp_update = mrp_data.update({'done_qty':mrp_data.done_qty + qty})
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',operation.oa_id.id)])
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':mrp_oa_data.oa_total_balance - qty})
            #oa_total_balance
            
        next = None
        w_center = operation.work_center.id
        if operation.next_operation in('Slider Assembly Output','Painting Output','Plating Output'):
            next = 'Assembly'
            
        process_flow = self.env["process.sequence"].search([]) #('item','=',self.fg_categ_type.name)
        cur_process = process_flow.filtered(lambda pr: pr.item == operation.fg_categ_type and pr.process == operation.next_operation)
        if cur_process:
            next_process = process_flow.filtered(lambda pr: pr.item == operation.fg_categ_type and pr.sequence == cur_process.sequence + 1)
            if next_process:
                next = next_process.process
                w_center = next_process.work_center.id
            else:
                next = 'Done'

        ope = operation.create({'mrp_lines':operation.mrp_lines,
                                'sale_lines':operation.sale_lines,
                                'mrp_line':operation.mrp_line,
                                'sale_order_line':operation.sale_order_line,
                                'parent_id':mo_ids,
                                'oa_id':operation.oa_id.id,
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
                                'operation_of':'output',
                                'work_center': w_center,
                                'operation_by':operation.work_center.name,
                                'based_on':'Lot Code',
                                'next_operation':next,
                                'qty':qty
                                })

    
    @api.onchange('uotput_qty')
    def _output(self):
        for out in self:
            
            done_qty = out.done_qty + out.uotput_qty
            out.done_qty = done_qty
            manufac_ids = self.env["manufacturing.order"].browse(out.mrp_lines)

            # get_field = self.env["manufacturing.order"]._get_field('dyeing_plan_qty') #getattr(manufacturing_order, 'dyeing_plan_qty')
            # # set_field = getattr(taps_manufacturing.manufacturing_order, 'dyeing_output')
            # raise UserError((get_field))
            
#'Assembly Output','Assembly Qc','Plating Output','Painting Output','Slider Assembly Output'
            #'Dyeing Output','Dyeing Qc','CM Output','Deeping Output','Deeping Qc'
            out_qty = out.uotput_qty
            for manu_o in manufac_ids:
                if out.next_operation == 'Dyeing Output':
                    if manu_o.dyeing_plan_qty <= out_qty:
                        m_qty = manu_o.dyeing_plan_qty
                        out_qty = out_qty - manu_o.dyeing_plan_qty
                    else:
                        m_qty = out_qty
                        out_qty = 0.00
                    m_qty += p.dyeing_output
                    manu_o.update({'dyeing_output':m_qty})
                    if out_qty == 0:
                        break
                elif out.next_operation == 'Dyeing Qc':
                    if manu_o.dyeing_plan_qty <= out_qty:
                        m_qty = manu_o.dyeing_plan_qty
                        out_qty = out_qty - manu_o.dyeing_plan_qty
                    else:
                        m_qty = out_qty
                        out_qty = 0.00
                    m_qty += p.dyeing_qc_pass
                    manu_o.update({'dyeing_qc_pass':m_qty})
                    if out_qty == 0:
                        break
                elif out.next_operation in ('Plating Output','Painting Output'):
                    if out.based_on == 'slider':
                        if manu_o.plating_plan_qty <= out_qty:
                            m_qty = manu_o.plating_plan_qty
                            out_qty = out_qty - manu_o.plating_plan_qty
                        else:
                            m_qty = out_qty
                            out_qty = 0.00
                        m_qty += p.plating_output
                        manu_o.update({'plating_output':m_qty})
                        if out_qty == 0:
                            break
                    if out.based_on == 'top':
                        if manu_o.top_plat_plan_qty <= out_qty:
                            m_qty = manu_o.top_plat_plan_qty
                            out_qty = out_qty - manu_o.top_plat_plan_qty
                        else:
                            m_qty = out_qty
                            out_qty = 0.00
                        m_qty += p.top_plat_output
                        manu_o.update({'top_plat_output':m_qty})
                        if out_qty == 0:
                            break
                    if out.based_on == 'bottom':
                        if manu_o.bot_plat_plan_qty <= out_qty:
                            m_qty = manu_o.bot_plat_plan_qty
                            out_qty = out_qty - manu_o.bot_plat_plan_qty
                        else:
                            m_qty = out_qty
                            out_qty = 0.00
                        m_qty += p.bot_plat_output
                        manu_o.update({'bot_plat_output':m_qty})
                        if out_qty == 0:
                            break
                    if out.based_on == 'pinbox':
                        if manu_o.pin_plat_plan_qty <= out_qty:
                            m_qty = manu_o.pin_plat_plan_qty
                            out_qty = out_qty - manu_o.pin_plat_plan_qty
                        else:
                            m_qty = out_qty
                            out_qty = 0.00
                        m_qty += p.pin_plat_output
                        manu_o.update({'pin_plat_output':m_qty})
                        if out_qty == 0:
                            break
                            
                elif out.next_operation == 'Slider Assembly Output':
                    if manu_o.sli_asmbl_plan_qty <= out_qty:
                        m_qty = manu_o.sli_asmbl_plan_qty
                        out_qty = out_qty - manu_o.sli_asmbl_plan_qty
                    else:
                        m_qty = out_qty
                        out_qty = 0.00
                    m_qty += p.sli_asmbl_output
                    manu_o.update({'sli_asmbl_output':m_qty})
                    if out_qty == 0:
                        break
                elif out.next_operation == 'Assembly Output':
                    if manu_o.dyeing_plan_qty <= out_qty:
                        m_qty = manu_o.dyeing_plan_qty
                        out_qty = out_qty - manu_o.dyeing_plan_qty
                    else:
                        m_qty = out_qty
                        out_qty = 0.00
                    m_qty += p.dyeing_output
                    manu_o.update({'dyeing_output':m_qty})
                    if out_qty == 0:
                        break
                

# 'CM Output','Deeping Output','Deeping Qc'
                        
#                 dyeing_output
# dyeing_qc_pass
            # if material == 'tape':
            #     if p.tape_con <= rest_pl_q:
            #         m_qty = p.tape_con
            #         rest_pl_q = rest_pl_q - p.tape_con
            #     else:
            #         m_qty = rest_pl_q
            #         rest_pl_q = 0.00
            #     re_pqty = m_qty 
            #     m_qty += p.dyeing_plan_qty
            #     p.update({'dyeing_plan':plan_start,'dyeing_plan_qty':m_qty,
            #              'dy_rec_plan_qty':re_pqty})
                
            
            #raise UserError((operation_d.ids))
            #ope = operation.update({'action_date':manuf_date,'done_qty':operation.done_qty + qty})
            
            if out.parent_id:
                parent_id = out.parent_id
                while (parent_id):
                    if out.parent_id != parent_id.id:
                        operation_p = self.env["operation.details"].browse(parent_id.id)
                        ope = operation_p.update({'done_qty':operation_p.done_qty + out.uotput_qty})
                    parent_id = parent_id.parent_id
    
            if out.next_operation == 'Assembly Qc':
                mrp_data = self.env["manufacturing.order"].browse(out.mrp_line.id)
                mrp_update = mrp_data.update({'done_qty':mrp_data.done_qty + out.uotput_qty})
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',out.oa_id.id)])
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':mrp_oa_data.oa_total_balance - out.uotput_qty})
                #oa_total_balance
                
            next = None
            w_center = out.work_center.id
            if out.next_operation in('Slider Assembly Output','Painting Output','Plating Output'):
                next = 'Assembly'
                
            process_flow = self.env["process.sequence"].search([]) #('item','=',self.fg_categ_type.name)
            cur_process = process_flow.filtered(lambda pr: pr.item == out.fg_categ_type and pr.process == out.next_operation)
            if cur_process:
                next_process = process_flow.filtered(lambda pr: pr.item == out.fg_categ_type and pr.sequence == cur_process.sequence + 1)
                if next_process:
                    next = next_process.process
                    w_center = next_process.work_center.id
                else:
                    next = 'Done'
            # operation = self.env["operation.details"].browse(self.id)
            ope = out.create({'mrp_lines':out.mrp_lines,
                                    'sale_lines':out.sale_lines,
                                    'mrp_line':out.mrp_line,
                                    'sale_order_line':out.sale_order_line,
                                    'parent_id':out.id,
                                    'oa_id':out.oa_id.id,
                                    'buyer_name':out.buyer_name,
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
                                    'operation_of':'output',
                                    'work_center':w_center,
                                    'operation_by':out.work_center.name,
                                    'based_on':'Lot Code',
                                    'next_operation':next,
                                    'qty':out.uotput_qty
                                    })









