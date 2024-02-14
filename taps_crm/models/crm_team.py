from odoo import fields, models



class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    # crm_team_line = fields.One2many('crm.team.line', 'crm_team_id', string='Team Line', copy=True)
    core_leader = fields.Many2one('res.users' , string='Core Leader', domain="[['active', 'in',[True,False] ]]")
    region = fields.Many2one('team.region' , string='Region') 



# class CrmTeamCustomerLine(models.Model):
#     _name = 'crm.team.line'
#     _description = 'Salesperson wise Customer Allocation'
    
    
    
    # quality_check_line = fields.One2many('quality.check.line', 'check_id', string='Order Lines', copy=True)
    # crm_team_id = fields.Many2one('crm.team', string='Team', index=True, required=True, ondelete='cascade')
    
    