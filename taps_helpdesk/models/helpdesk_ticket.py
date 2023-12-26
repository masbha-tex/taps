from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class tapsHelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    

    oa_number = fields.Many2one('sale.order', string='Oa Number')
    buyer = fields.Many2one('res.partner', string='Buyer')
    complain = fields.Text(string='Detail Complaint')
    ccr_count = fields.Integer(compute='_compute_ccr_number', string='Ccr count', store=True)
    ccr_ids = fields.Many2many('sale.ccr', compute='_compute_ccr_number', string='Ccr', copy=False, store=True)

    @api.onchange('ccr_ids')
    def _compute_ccr_number(self):
        
        for order in self:
            ccr = order.env['sale.ccr'].search([('ticket_id', '=', self.id)])
            order.ccr_ids = ccr
            # raise UserError((len(ccr)))
            order.ccr_count = len(ccr)

    def name_get(self):
        result = []
        for ticket in self:
            # result.append((ticket.id, "%s (#%d)" % (ticket.name, ticket._origin.id)))
            result.append((ticket.id, "(#%d) %s" % (ticket._origin.id, ticket.name)))
        
        return result
        
    @api.onchange('oa_number')
    def _set_buyer_customer(self):
        # raise UserError((self.oa_number.partner_id.id))
        self.buyer = self.env['res.partner'].search([('id', '=', self.oa_number.buyer_name.id)])
        self.partner_id = self.env['res.partner'].search([('id', '=', self.oa_number.partner_id.id)])
        # return {}

    def create_view_ccr(self):
        result = self.env["ir.actions.actions"]._for_xml_id('taps_sale.action_sale_ccr')
        # action_sale_ccr
        
        result['context'] = {'default_oa_number': self.oa_number.id, 'default_ticket_id' : self.id}
        
        ccr_ids = self.env['sale.ccr'].search([('ticket_id', '=', self.id)])
        
        if  len(ccr_ids) >= 1:
            
            result['domain'] = "[('id','in',%s)]" % (ccr_ids.ids)
            # raise UserError((len(ccr_ids)))
            self._compute_ccr_number()
        elif not ccr_ids or len(ccr_ids) == 0:
            
            res = self.env.ref('taps_sale.view_sale_ccr_form', False)
            # raise UserError((res))
            
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
                
                
            else:
                
                result['views'] = form_view
                
            result['res_id'] = ccr_ids.id
            self._compute_ccr_number()
        # raise UserError(((result['res_id'])))
        # res = self.env.ref('taps_sale.view_sale_ccr_form', False)
        # form_view = [(res and res.id or False, 'form')]
        # result['views'] = form_view 
        
        return result

    
        
    # def action_view_picking(self):
    #     """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
    #     """
    #     result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
    #     # override the context to get rid of the default filtering on operation type
    #     result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name, 'default_picking_type_id': self.picking_type_id.id}
    #     pick_ids = self.mapped('picking_ids')
    #     # choose the view_mode accordingly
    #     if not pick_ids or len(pick_ids) > 1:
    #         result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
    #     elif len(pick_ids) == 1:
    #         res = self.env.ref('stock.view_picking_form', False)
    #         form_view = [(res and res.id or False, 'form')]
    #         if 'views' in result:
    #             result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
    #         else:
    #             result['views'] = form_view
    #         result['res_id'] = pick_ids.id
    #     return result

    # @api.model
    # def _name_search(self,name,id, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain =[]
    #     if name:
    #         domain=['|', ('name', operator, name),('id', operator, id)]
    #     return self._search(domain+args , limit=limit, access_rights_uid=name_get_uid)


