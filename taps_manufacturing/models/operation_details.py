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
    
    fg_categ_type = fields.Char(string='Item', related='product_template_id.fg_categ_type.name', store=True)
    
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
    sizemm = fields.Char(string='Size (MM)', store=True, readonly=True)
    sizcommon = fields.Char(string='Size', store=True, readonly=False, compute='compute_size')

    @api.depends('sizein', 'sizecm', 'sizemm')
    def compute_size(self):
        for s in self:
            if s.sizein !=False and s.sizein != 'N/A':
                s.sizcommon = str(s.sizein) + ' In' 
            elif s.sizecm !=False and s.sizecm != 'N/A':
                s.sizcommon = str(s.sizecm) + ' Cm'
            elif s.sizemm !=False and s.sizemm != 'N/A':
                s.sizcommon = str(s.sizemm) + ' Mm'
    
    top = fields.Char(string='Top', store=True, readonly=True)
    bottom = fields.Char(string='Bottom', store=True)
    pinbox = fields.Char(string='Pin-Box', store=True)
    logo = fields.Text(string='Logo', store=True, readonly=True)
    logoref = fields.Text(string='Logo Ref', store=True, readonly=True)
    logo_type = fields.Text(string='Logo Type', store=True, readonly=True)
    style = fields.Text(string='Style', store=True, readonly=True)
    gmt = fields.Text(string='Gmt', store=True, readonly=True)
    shapefin = fields.Text(string='Shape Finish', store=True, readonly=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True, readonly=True)
    b_part = fields.Text(string='B Part', store=True, readonly=True)
    c_part = fields.Text(string='C Part', store=True, readonly=True)
    d_part = fields.Text(string='D Part', store=True, readonly=True)
    finish_ref = fields.Text(string='Finish Ref', store=True, readonly=True)
    product_code = fields.Text(string='Product Code', store=True, readonly=True)
    shape = fields.Text(string='Shape', store=True, readonly=True)
    back_part = fields.Text(string='Back Part', store=True, readonly=True)

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
            if s.next_operation in ('Dyeing Qc','Packing Output'):
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
    
    actual_qty = fields.Float(string='OA Qty', readonly=True, store=True, group_operator="sum")
    ac_balance_qty = fields.Float(string='OA Balance', readonly=False, store=True, compute='get_ac_balance', group_operator="sum")
    qty = fields.Float(string='Qty', readonly=False)
    price_unit = fields.Float('Unit Price', digits='Product Price', default=0.0, store=True)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=False, store=True, compute='get_balance', group_operator="sum")
    uotput_qty = fields.Float(string='Output', default=0.0, readonly=False)
    pack_qty = fields.Integer(string='Pack Qty', readonly=False)
    fr_pcs_pack = fields.Integer(string='Remaining Qty', readonly=False, help='The remaining pcs to pack')
    fg_done_qty = fields.Integer(string='FG Done', default=0, readonly=False)
    fg_balance = fields.Integer(string='FG Balance', readonly=False, store=True, compute='get_fg_balance', group_operator="sum")
    fg_output = fields.Integer(string='FG Output', default=0, readonly=False, group_operator="sum")
    # cartoon_no = fields.Many2one('operation.details', string='Cartoon No', required=False, domain="[('next_operation', '=', 'Delivery')]")
    cartoon_no = fields.Many2one('fg.packaging', string='Carton No', required=False, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('oa_id', '=', oa_id)]")
    
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
        ('hold', 'Hold'),
        ('cancel', 'Cancelled'),
        ('closed', 'Closed')],
        string='State')
    revision_no = fields.Char(string='Revision No', store=True)
    closing_date = fields.Datetime(string='Closing Date', readonly=False)
    return_qty = fields.Float(string='Return Qty', default=0.0, readonly=False)
    
    sale_line_of_top = fields.Integer(string='Sale Line of Top', store=True, readonly=True)
    carton_weight = fields.Float(string='Weight', default=0.0, readonly=False)
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
                if order.work_center.name == 'Dyeing':
                    production = self.env["manufacturing.order"].search([('oa_id','=',order.oa_id.id),('shade','=',order.shade),('plan_ids','!=',False)])
                else:
                    m_lines = order.mrp_lines
                    m_lines = [int(i) for i in sorted(m_lines.split(','))]
                    production = self.env["manufacturing.order"].search([('id','in',m_lines)])
                if order.mr_req:
                    if order.mr_req.state not in ('done','cancel'):
                        picking = self.env["stock.picking"].search([('id','=',order.mr_req.id)]).action_cancel()
                    
                        same_mr = self.env["operation.details"].search([('id','!=',order.id),('mr_req','=',order.mr_req.id)])
                        mr_update = same_mr.update({'qty':0})
                # if order.id not in(207,0):
                #     raise UserError((order.id,str(order.plan_id),str(production[0].plan_ids),order.oa_id.id,order.shade))
                production = production.filtered(lambda op: str(order.plan_id) in op.plan_ids)
                if production:
                    res_qty = order.qty
                    for p in production:
                        dn_qty = 0
                        plqty = 0
                        if order.based_on == 'tape':
                            plqty = p.dyeing_plan_qty
                            m_con = p.tape_con
                        if order.based_on == 'slider':
                            plqty = p.plating_plan_qty
                            m_con = p.slider_con
                        if order.based_on == 'top':
                            plqty = p.top_plat_plan_qty
                            m_con = p.topwire_con
                        if order.based_on == 'bottom':
                            plqty = p.bot_plat_plan_qty
                            m_con = p.botomwire_con
                        if order.based_on == 'pinbox':
                            plqty = p.pin_plat_plan_qty
                            m_con = p.pinbox_con
                            
                            
                        if plqty > 0:
                            if plqty >= res_qty:
                                qty = plqty - res_qty
                                dn_qty = res_qty
                            else:
                                qty = plqty - plqty
                                dn_qty = plqty
                            if m_con > 0.01 and qty <= 0.01:
                                qty = 0
                            if order.based_on == 'tape':
                                p.update({'dyeing_plan':None,'dyeing_plan_qty':qty,'dy_rec_plan_qty':None})
                            if order.based_on == 'slider':
                                p.update({'plating_plan':None,'plating_plan_qty':qty,'pl_rec_plan_qty':None})
                            if order.based_on == 'top':
                                p.update({'top_plat_plan':None,'top_plat_plan_qty':qty,'tpl_rec_plan_qty':None})
                            if order.based_on == 'bottom':
                                p.update({'bot_plat_plan':None,'bot_plat_plan_qty':qty,'bpl_rec_plan_qty':None})
                            if order.based_on == 'pinbox':
                                p.update({'pin_plat_plan':None,'pin_plat_plan_qty':qty,'ppl_rec_plan_qty':None})
                            
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

    def button_return(self):
        self.ensure_one()
        self._check_company()
        if self.next_operation != 'FG Packing':
            raise UserError(('This is not for you'))
            
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_return")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action


    def button_change_packing_date(self):
        # self.ensure_one()
        self._check_company()
        for record in self:
            if record.next_operation != 'FG Packing':
                raise UserError(('This is not for you'))
        unique_dates = set(record.action_date.date() for record in self)
        if len(unique_dates) > 1:
            raise UserError(('You can change date only for one date'))
            
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.change_production_date")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action        
            
        
       
        
    def button_group_output(self):
        for r in self:
            if r.next_operation in ('Chain Making','Gapping'):
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
    
    def set_requisition(self,company_id,active_model,ope_id,work_center,product_id,product_line,qty=None):
        operation = self.env["operation.details"].search([])
        mrp_lines = sale_lines = parent_ids = oa_ids = None
        finish = None
        if active_model == 'manufacturing.order':
            # raise UserError(('sdfdfds'))
            m_order = self.env["manufacturing.order"].browse(ope_id)
            finish = m_order[0].finish
            mrp_lines = ope_id
            sale_lines = ','.join([str(i) for i in sorted(m_order.sale_order_line.ids)])
            oa_ids = ','.join([str(i) for i in sorted(m_order.oa_id.ids)])
            oa_ids = [int(id_str) for id_str in oa_ids.split(',')]
            sale_order = self.env["sale.order"].browse(oa_ids)
            oa_list = sale_order.mapped('name')
            
            # raise UserError((oa_list))
            #operation._ids2str('sale_order_line')
        else:
            operation = operation.browse(ope_id)
            finish = operation[0].finish
            parent_ids = operation._ids2str('ids')
            oa_ids = operation._ids2str('oa_id')
            sale_order = self.env["sale.order"].search([('id', 'in', (oa_ids,0))])#(oa_ids)
            oa_list = sale_order.mapped('name')

        locations = self.env["stock.location"].search([('company_id','=',self.env.company.id),('name', 'in', ('Stock','Production'))])
        locationid = locations.filtered(lambda pr: pr.name == 'Stock').id
        
        des_locationid = locations.filtered(lambda pr: pr.name == 'Production').id

        picking_types = self.env["stock.picking.type"].search([('company_id','=',self.env.company.id),('sequence_code', '=', 'MR' )])#('Z_Manufacturing','M_Manufacturing')
        pic_typeid = picking_types.id
        warehouse_id = picking_types.warehouse_id.id
        
        # raise UserError((self.env.user.partner_id.id,self.env.company.id,self.env.user.user_id))
        pick = self.env["stock.picking"].create({'priority':'1',
                                                 'move_type':'direct',
                                                 'state':'draft',
                                                 'scheduled_date':datetime.now(),
                                                 'location_id':locationid,
                                                 'location_dest_id':des_locationid,
                                                 'picking_type_id':pic_typeid,
                                                 'partner_id':self.env.user.partner_id.id,
                                                 'company_id':self.env.company.id,
                                                 'user_id':self.env.user.user_id,
                                                 'immediate_transfer':False,
                                                 'operation_lines':parent_ids,
                                                 'mrp_lines':mrp_lines,
                                                 'oa_ids':oa_ids,
                                                 'x_studio_oa_no':oa_list,
                                                 'note':finish
                                                 })
        
        if product_line:
            for prod in product_line:
                raise UserError(('fe'))
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
                                        'mr_req':pick.id,
                                        'qty':prod.product_qty
                                        })
    
                stockmove = self.env["stock.move"].create({'name':prod.product_id.product_tmpl_id.display_name,
                                                           'company_id':self.env.company.id,
                                                           'product_id':prod.product_id.id,
                                                           'description_picking':prod.product_id.product_tmpl_id.name,
                                                           # 'product_qty':prod.product_qty,
                                                           'product_uom_qty':prod.product_qty,
                                                           'product_uom':prod.product_id.product_tmpl_id.uom_id.id,
                                                           'location_id':locationid,
                                                           'location_dest_id':des_locationid,
                                                           'partner_id':self.env.user.partner_id.id,
                                                           'picking_id':pick.id,
                                                           'state':'draft',
                                                           'procure_method':'make_to_stock',
                                                           'picking_type_id':pic_typeid,
                                                           'reference':pick.name
                                                           })
                
        elif product_id:
            ope = operation.create({'mrp_lines':mrp_lines,
                                    'sale_lines':sale_lines,
                                    'parent_ids':parent_ids,
                                    'company_id':self.env.company.id,
                                    'action_date':datetime.now(),
                                    'operation_of':'req',
                                    'work_center':work_center,
                                    'operation_by':self.env.user.name,
                                    'product_id':product_id.id,
                                    'based_on':'process',
                                    'next_operation':'Issue',
                                    'mr_req':pick.id,
                                    'qty':qty
                                    })
    
            stockmove = self.env["stock.move"].create({'name':product_id.product_tmpl_id.display_name,
                                                       'company_id':self.env.company.id,
                                                       'product_id':product_id.id,
                                                       'description_picking':product_id.product_tmpl_id.name,
                                                       # 'product_qty':prod.product_qty,
                                                       'product_uom_qty':qty,
                                                       'product_uom':product_id.product_tmpl_id.uom_id.id,
                                                       'location_id':locationid,
                                                       'location_dest_id':des_locationid,
                                                       'partner_id':self.env.user.partner_id.id,
                                                       'picking_id':pick.id,
                                                       'state':'draft',
                                                       'procure_method':'make_to_stock',
                                                       'picking_type_id':pic_typeid,
                                                       'reference':pick.name
                                                       })
            
        st_app_entry = self.env["studio.approval.entry"].sudo().create({'rule_id':19,
                                                       'model':'stock.picking',
                                                       'method':'action_confirm',
                                                       'res_id':pick.id,
                                                       'approved':True,
                                                       })
            
        return pick.id


    # id,name,user_id,rule_id,model,method,action_id,res_id,approved,create_uid,create_date,write_uid,write_date
    
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

                size = l.sizein
                if size == 'N/A':
                    size = l.sizecm

                for l_q in range(lots):
                    size_wise = m_orders.filtered(lambda op: op.sizein == size or op.sizecm == size)
                    while rest_q > 0:
                        for s in size_wise:
                            
                            if rest_q > l_capa:
                                qty = l_capa
                            else:
                                qty = rest_q

                            s_qty = qty
                            if s.balance_qty > qty:
                                s_qty = qty
                            else:
                                s_qty = s.balance_qty
                            # raise UserError((m_orders[0].fg_categ_type))
                            next = 'Assembly Output'
                            work_center = operation[0].work_center.id
                            if 'Metal' in m_orders[0].fg_categ_type or 'AL' in m_orders[0].fg_categ_type:
                                next = 'Dipping Output'
                                work_center = 17
                            # 'mrp_line':l.mrp_line.id,
                            # 'sale_order_line':l.mrp_line.sale_order_line.id,
                            # for mr_li in l.mrp_line:
                           
                            ope = operation.create({'mrp_lines':s.id,
                                                    'sale_lines':s.sale_order_line.id,
                                                    'oa_id':s.oa_id.id,
                                                    'buyer_name':s.buyer_name,
                                                    'product_id':s.product_id.id,
                                                    'product_template_id':s.product_template_id.id,
                                                    'action_date':datetime.now(),
                                                    'shade':s.shade,
                                                    'shade_ref':s.shade_ref,
                                                    'finish':s.finish,
                                                    'slidercodesfg':s.slidercodesfg,
                                                    'top':s.ptopfinish,
                                                    'bottom':s.pbotomfinish,
                                                    'pinbox':s.ppinboxfinish,
                                                    'sizein':s.sizein,
                                                    'sizecm':s.sizecm,
                                                    'operation_of':'lot',
                                                    'work_center':work_center,
                                                    'operation_by':operation[0].work_center.name,
                                                    'based_on':operation[0].based_on,
                                                    'next_operation':next,
                                                    'actual_qty':s.product_uom_qty,
                                                    'qty':s_qty
                                                    })
                            rest_q = rest_q - s_qty

    def set_delivery_order(self,active_model,ope_id,delivery,delivery_line):
        operation = self.env["operation.details"].browse(ope_id)

        picking = self.env["stock.picking"].search([('origin','=',operation[0].oa_id.name),
                                                    ('state','not in',('draft','done','cancel'))])
        picking.update({'scheduled_date':delivery.deliveri_date})
        
        for l in operation:
            stock_move_line = self.env["stock.move.line"].search([('product_id','=',l.product_id.id),('reference','=',picking.name),('lot_id','=',l.move_line.lot_id.id)])
            stock_move_line.update({'qty_done':l.qty})

        operation.update({'state':'done','mrp_delivery':picking.id,'total_weight':delivery.total_weight,'action_date':delivery.deliveri_date})
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

        # raise UserError((vals.get('next_operation')))
        if vals.get('operation_of') == "lot" or (vals.get('next_operation') == "Packing Output"):
            ref = self.env['ir.sequence'].next_by_code('mrp.lot', sequence_date=seq_date)
            vals['name'] = ref
        if vals.get('next_operation') == "Delivery":
            if 'cartoon_no' in vals:
                weight = 0
                if vals.get('carton_weight'):
                    weight = vals.get('carton_weight')
                if vals.get('cartoon_no'):
                    vals['cartoon_no'] = vals.get('cartoon_no')
                    packing = self.env['fg.packaging'].browse(vals.get('cartoon_no'))
                    packing.update({'total_weight':weight,'oa_id':vals.get('oa_id')})
                else:
                    # raise UserError((vals.get('oa_id'),'dds'))
                    packing = self.env['fg.packaging'].create({'company_id':self.env.company.id ,'total_weight':weight,'oa_id':self.oa_id.id})
                    packing.update({'total_weight':weight,'oa_id':vals.get('oa_id')})
                    # ref = self.env['ir.sequence'].next_by_code('fg.cartoon', sequence_date=seq_date)
                    vals['cartoon_no'] = packing.id
        vals['state'] = 'waiting'
        result = super(OperationDetails, self).create(vals)
        return result                

    # @api.model
    def write(self, vals):
        if 'done_qty' in vals:
            if self.state not in('done','closed'):
                a = ''
                if self.next_operation in ('Dyeing Qc','Packing Output'):
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
            # raise UserError((vals.get('cartoon_no')))
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
                    out = self.env['operation.details'].search([('cartoon_no', '=', vals.get('cartoon_no')),('next_operation', '=', 'FG Packing')])
                    #self.env['operation.details'].filtered(lambda op: op.id == 120)
                    #.sorted(key=lambda pr: pr.id)[:1]
                    if out:
                        name = out.name
                #     out.update({'qty': out.qty + vals.get('fg_output')})
                # else:
                # raise UserError((qty,vals.get('fg_output')))
                # raise UserError((vals.get('cartoon_no')))
                packaging = self.env['fg.packaging'].browse(vals.get('cartoon_no'))
                ope = self.env['operation.details'].create({'name':packaging.internal_ref,
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
                                                            'move_line':self.move_line.id,
                                                            'cartoon_no':vals.get('cartoon_no'),
                                                            'carton_weight':vals.get('carton_weight')
                                                            })
                vals['fg_output'] = 0
                vals['cartoon_no'] = ope.cartoon_no.id
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
    def set_group_output(self,mo_ids,qty,planned_qty):
        # raise UserError(('Under Construction'))
        operation = self.env["operation.details"].browse(mo_ids)
        qty_ = round((qty/len(operation)),2)
        # 'Dyeing Qc'
        # raise UserError((qty))
        if operation[0].next_operation == 'Dyeing Qc':
            rest_qty = qty
            while rest_qty > 0:
                for op in operation:
                    o_qty = op.done_qty + rest_qty
                    if op.ac_balance_qty >= o_qty:
                        op.write({'uotput_qty': rest_qty})
                        op._output()
                        rest_qty = 0
                    else:
                        if op.ac_balance_qty > op.done_qty:
                            o_qty = op.ac_balance_qty - op.done_qty
                            if o_qty > 0:
                                op.write({'uotput_qty': o_qty})
                                rest_qty = rest_qty - o_qty
                                op._output()
                            else:
                                rest_qty = 0
        else:
            for op in operation:
                if planned_qty == qty:
                    qty_ = op.balance_qty
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

            if (out.next_operation not in ('Dyeing Output')) and (round(out.balance_qty,0) < round(out.uotput_qty,0)):
                raise UserError(('You can not produce more then balance'))
            if (out.state not in ('partial','waiting')):
                raise UserError(('You can not update this data because of state is done/closed'))
            # else:
            s = out.write({'done_qty':done_qty})#done_qty = done_qty
            manufac_ids = self.env["manufacturing.order"].browse(out.mrp_lines)
            mrp_lines = [int(id_str) for id_str in out.mrp_lines.split(',')]
            mrp_data = self.env["manufacturing.order"].browse(mrp_lines)

            # get_field = self.env["manufacturing.order"]._get_field('dyeing_plan_qty') #getattr(manufacturing_order, 'dyeing_plan_qty')
            # # set_field = getattr(taps_manufacturing.manufacturing_order, 'dyeing_output')
            # raise UserError((get_field))
            
#'Assembly Output','Assembly Qc','Plating Output','Painting Output','Slider Assembly Output'
            #'Dyeing Output','Dyeing Qc','CM Output','Deeping Output','Deeping Qc'
            # out_qty = out.uotput_qty
            if out.next_operation in('Dyeing Output','Dyeing Qc','CM Output','Dipping Output','Assembly Output','Packing Output','Plating Output','Painting Output','Slider Assembly Output'):
                up = self.set_mrp_output(out.next_operation,out.mrp_lines,out.uotput_qty,out.based_on)
            
            # if out.parent_id:
            #     parent_id = out.parent_id
            #     while (parent_id):
            #         if out.parent_id != parent_id.id:
            #             operation_p = self.env["operation.details"].browse(parent_id.id)
            #             dqt = operation_p.done_qty + out.uotput_qty
            #             ope = operation_p.write({'done_qty':dqt})
            #         parent_id = parent_id.parent_id
    
            move_line = None
            if out.next_operation == 'Packing Output':
                # mrp_ids = [int(i) for i in sorted(mrp_ids.split(','))]
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
                    extra = out_qty
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
                            if outqty == 0:
                                each_qty = 0
                                extra = each_qty
                            else:
                                each_qty = each_qty - outqty
                else:
                    raise UserError(('Ignore this line, this is invalid'))
                move_qty = out.uotput_qty
                if (extra > 0) and (out.uotput_qty != extra):
                    move_qty = out.uotput_qty - extra
                mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',out.oa_id.id)])
                tot_b =  sum(mrp_oa_data.mapped('oa_total_balance'))/ len(mrp_oa_data) # mrp_oa_data.oa_total_balance - out.uotput_qty
                tot_b = tot_b - move_qty #out.uotput_qty
                if tot_b == 0:
                    mrp_all_oa = mrp_oa_data.update({'oa_total_balance':tot_b,'closing_date':datetime.now(),'state':'closed'})
                    # op_closed = self.env["operation.details"].browse(out.oa_id.id)
                    # _closed = op_closed.update({'closing_date':datetime.now(),'state':'closed'})
                    sl_closed = self.env["sale.order"].browse(out.oa_id.id)
                    _slclosed = sl_closed.write({'closing_date':datetime.now().date()})
                else:
                    mrp_all_oa = mrp_oa_data.update({'oa_total_balance':tot_b})
# id,name,sequence,company_id,product_id,product_qty,product_uom_qty,product_uom,location_id,location_dest_id,state,origin,procure_method,scrapped,group_id,propagate_cancel,picking_type_id,warehouse_id,additional,reference,is_done,production_id,unit_factor,weight   
                locations = self.env["stock.location"].search([('company_id','=',self.env.company.id),('name', 'in', ('Stock','Production'))])
                locationid = locations.filtered(lambda pr: pr.name == 'Stock').id
                
                des_locationid = locations.filtered(lambda pr: pr.name == 'Production').id

                picking_types = self.env["stock.picking.type"].search([('company_id','=',self.env.company.id),('code', '=', 'mrp_operation' )])#('Z_Manufacturing','M_Manufacturing')
                pic_typeid = picking_types.id
                warehouse_id = picking_types.warehouse_id.id
                
                if move_qty > 0:
                    stockmove = self.env["stock.move"].create({'name':'New',
                                                               'sequence':10,
                                                               'company_id':self.env.company.id,
                                                               'product_id':out.product_id.id,
                                                               # 'product_qty':out.uotput_qty,
                                                               'product_uom_qty':move_qty,
                                                               'product_uom':out.product_id.product_tmpl_id.uom_id.id,
                                                               'location_id':des_locationid,
                                                               'location_dest_id':locationid,
                                                               'state':'done',
                                                               'procure_method':'make_to_stock',
                                                               'scrapped':False,
                                                               # 'group_id':11129,
                                                               'propagate_cancel':False,
                                                               'picking_type_id':pic_typeid,
                                                               'warehouse_id':warehouse_id,
                                                               'additional':False,
                                                               # 'reference':,
                                                               'is_done':True,
                                                               # 'production_id':,
                                                               'unit_factor':move_qty
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
                                                                         'qty_done':move_qty,
                                                                         'lot_id':lot_producing_id.id,
                                                                         'date':datetime.now(),
                                                                         'location_id':des_locationid,
                                                                         'location_dest_id':locationid,
                                                                         'state':'done',# 'reference':,
                                                                         'qty_onhand':move_qty
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
                items = tape_in_qc.mapped('product_template_id')
                m_lines = tape_in_qc.mapped('mrp_lines')
                m_lines = ','.join([str(i) for i in sorted(m_lines)])
                m_lines = [int(id_str) for id_str in m_lines.split(',')]
                m_order = self.env["manufacturing.order"].browse(m_lines)
                
                shades = m_order.mapped('shade')
                
                # raise UserError((shades))
                # mrp_lines = [int(id_str) for id_str in out.mrp_lines.split(',')]
                # mrp_data = self.env["manufacturing.order"].browse(mrp_lines)

                
                # shades = ','.join([str(i) for i in sorted(shades)])
                # oa_ids = ','.join([str(i) for i in sorted(oa_ids)])
                # oa_ids = [int(i) for i in sorted(oa_ids.split(','))]
                
                rest_qty = out.uotput_qty
                while rest_qty > 0:
                    excessqty = 0
                    row_creates = 0
                    ope_ids = []
                    # raise UserError((sorted(oa_ids),len(oa_ids)))
                    for i, oa in enumerate(sorted(oa_ids)):
                        for sh in shades:
                            #     for item in items:
                            # ('mrp_lines','=', out.mrp_lines),
                            # mrp_data = mrp_data.filtered(lambda pr: pr.shade == out.shade and pr.oa_id.id == out.oa_id.id)
                            # existing_qc = self.env["manufacturing.order"].search([('oa_id','=', oa.id),('id','in', out.shade)])
                            existing_qc = None
                            # raise UserError((shades))
                            # for sh in shades:
                            existing_qc = self.env["operation.details"].search([('oa_id','=', oa.id),('shade','=', sh),('next_operation','=', 'Dyeing Qc')])
                                # if existing_qc:
                                #     break
                            #('shade','=', sh),('product_template_id','=', item.id)
                            # tape_in_qc.filtered(lambda dy: dy.oa_id.id == oa.id and dy.shade == out.shade and dy.next_operation == 'Dyeing Qc')
                            qc_qty = 0
                    
                            if existing_qc:
                                qc_qty = existing_qc.qty + rest_qty
                                if existing_qc.actual_qty >= qc_qty:
                                    ope_ids.append(existing_qc.id)
                                    qc_update = existing_qc.update({'qty':qc_qty})
                                    rest_qty = rest_qty - rest_qty
                                    excessqty = 0
                                else:
                                    if existing_qc.actual_qty > existing_qc.qty:
                                        qc_qty = existing_qc.actual_qty - existing_qc.qty
                                        if qc_qty > 0:
                                            ope_ids.append(existing_qc.id)
                                            # raise UserError((existing_qc.qty,qc_qty))
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
                                # raise UserError(('ere',rest_qty,i+1))
                                row_creates += 1
                                # _mrp_data = mrp_data.filtered(lambda pr: pr.shade == sh and pr.oa_id.id == oa.id and pr.product_template_id.id == item.id)
                                mrp_data = self.env["manufacturing.order"].search([('oa_id','=',oa.id),('shade','=',sh)])#tape_in_qc.mapped('shade')
                                if mrp_data:
                                    # actual_qty = sum(mrp_data.mapped('tape_con'))
                                    # raise UserError(('grrgrg',actual_qty))
                                    actual_qty = sum(mrp_data.mapped('tape_con'))
                                    a = ''
                                    if actual_qty >= rest_qty:
                                        qc_qty = rest_qty
                                        rest_qty = rest_qty - qc_qty
                                    else:
                                        qc_qty = actual_qty
                                        rest_qty = rest_qty - qc_qty
        
                                    # raise UserError((rest_qty,qc_qty))
                                    ope = self.env['operation.details'].create({'name':out.name,
                                                                                'mrp_lines':out.mrp_lines,
                                                                                'sale_lines':out.sale_lines,
                                                                                'mrp_line':out.mrp_line.id,
                                                                                'sale_order_line':out.sale_order_line.id,
                                                                                'parent_id':out.id,
                                                                                'oa_id':oa.id,
                                                                                'buyer_name':out.buyer_name,
                                                                                'product_id':out.product_id.id,
                                                                                'product_template_id':mrp_data[0].product_template_id.id,
                                                                                'action_date':out.action_date,
                                                                                'shade':sh,
                                                                                'shade_ref':mrp_data[0].shade_ref,
                                                                                'finish':mrp_data[0].finish,
                                                                                'sizein':mrp_data[0].sizein,
                                                                                'sizecm':mrp_data[0].sizecm,
                                                                                'slidercodesfg':mrp_data[0].slidercodesfg,
                                                                                'top':mrp_data[0].ptopfinish,
                                                                                'bottom':mrp_data[0].pbotomfinish,
                                                                                'pinbox':mrp_data[0].ppinboxfinish,
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
                                    ope_ids.append(ope.id)
                            # raise UserError((rest_qty))
                            if rest_qty == 0:
                                break
                    #i+1 == len(oa_ids)
                    if excessqty > 0:
                        excessqty = round((excessqty/len(oa_ids)),2)
                        # op_ids = ','.join([str(i) for i in sorted(ope_ids)])
                        # op_ids = [int(i) for i in sorted(op_ids.split(','))]
                        # operation = self.env["operation.details"].browse(op_ids)
                        # excessqty = round((excessqty/len(operation)),2)
                        rest_qty = 0
                        # existing_qc = None
                        # for l in sorted(oa_ids):
                        #     existing_qc = self.env["operation.details"].search([('oa_id','=', l.id),('shade','=', out.shade),('next_operation','=', 'Dyeing Qc')])
                        #     qc_update = existing_qc.update({'qty': existing_qc.qty + excessqty})
            
            else:
                can_create = True
                if out.next_operation == 'Assembly Output':
                    pack_exist = self.env['operation.details'].search([('mrp_lines','=',out.mrp_lines),('sizein','=',out.sizein),('sizecm','=',out.sizecm),('oa_id','=',out.oa_id.id),('next_operation','=','Packing Output')])
                    if pack_exist:
                        can_create = False
                        up_pack = pack_exist.update({'qty':pack_exist.qty + out.uotput_qty})
                if next == 'Packing Output':
                    mrp_l_ids = int(out.mrp_lines)
                    oa_qty = self.env['manufacturing.order'].browse(mrp_l_ids)
                    actual_qty = sum(oa_qty.mapped('product_uom_qty'))
                if (next == '' or next == None) and w_center in (7,14):
                    next = 'FG Packing'
                if can_create:
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
                                                            'logo':out.logo,
                                                            'logoref':out.logoref,
                                                            'logo_type':out.logo_type,
                                                            'style':out.style,
                                                            'gmt':out.gmt,
                                                            'shapefin':out.shapefin,
                                                            'b_part':out.b_part,
                                                            'c_part':out.c_part,
                                                            'd_part':out.d_part,
                                                            'finish_ref':out.finish_ref,
                                                            'product_code':out.product_code,
                                                            'shape':out.shape,
                                                            'back_part':out.back_part,
                                                            'sizein':out.sizein,
                                                            'sizecm':out.sizecm,
                                                            'sizemm':out.sizemm,
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
                                                            'move_line':move_line,
                                                            'price_unit':out.price_unit,
                                                            })
            out.uotput_qty = 0



