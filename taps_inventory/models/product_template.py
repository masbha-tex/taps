# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class IncludeCateTypeInPT(models.Model):
    _inherit = 'product.template'
    categ_type = fields.Many2one('category.type', 'Category Type', check_company=True, change_default=True)
    
    pur_description = fields.Selection([
        ('Auto Taffeta', 'Auto Taffeta'),
        ('Brass Wire', 'Brass Wire'),
        ('C#3 Long Chain', 'C#3 Long Chain'),
        ('C#3 Long Chain GRS', 'C#3 Long Chain GRS'),
        ('C#3 Special Slider', 'C#3 Special Slider'),
        ('C#3 STD Slider', 'C#3 STD Slider'),
        ('C#3 WP Long Chain', 'C#3 WP Long Chain'),
        ('C#5 Body, Cap & Spring', 'C#5 Body, Cap & Spring'),
        ('C#5 Long Chain', 'C#5 Long Chain'),
        ('C#5 Long Chain GRS', 'C#5 Long Chain GRS'),
        ('C#5 Special Slider', 'C#5 Special Slider'),
        ('C#5 STD Slider', 'C#5 STD Slider'),
        ('C#5 WP Long Chain', 'C#5 WP Long Chain'),
        ('Dipping Chemical', 'Dipping Chemical'),
        ('Dyeing', 'Dyeing'),
        ('ETP', 'ETP'),
        ('M#4  U Top stopper', 'M#4  U Top stopper'),
        ('M#4 Cotton Tape', 'M#4 Cotton Tape'),
        ('M#4 H Bottom', 'M#4 H Bottom'),
        ('M#4 Special Slider', 'M#4 Special Slider'),
        ('M#4 STD Slider', 'M#4 STD Slider'),
        ('M#4 Tape DN+', 'M#4 Tape DN+'),
        ('M#4 Tape GRS', 'M#4 Tape GRS'),
        ('M#4 Top Wire', 'M#4 Top Wire'),
        ('M#5  U Top stopper', 'M#5  U Top stopper'),
        ('M#5 Body, Cap & Spring', 'M#5 Body, Cap & Spring'),
        ('M#5 Cotton Tape', 'M#5 Cotton Tape'),
        ('M#5 H Bottom', 'M#5 H Bottom'),
        ('M#5 PIN AND BOX', 'M#5 PIN AND BOX'),
        ('M#5 Special Slider', 'M#5 Special Slider'),
        ('M#5 STD Slider', 'M#5 STD Slider'),
        ('M#5 Tape', 'M#5 Tape'),
        ('M#5 Tape GRS', 'M#5 Tape GRS'),
        ('M#8  U Top stopper', 'M#8  U Top stopper'),
        ('M#8 H Bottom', 'M#8 H Bottom'),
        ('M#8 PIN AND BOX', 'M#8 PIN AND BOX'),
        ('M#8 Polyester tape', 'M#8 Polyester tape'),
        ('M#8 Special Slider', 'M#8 Special Slider'),
        ('N#3 ALU Bottom', 'N#3 ALU Bottom'),
        ('N#3 ALU Top Wire', 'N#3 ALU Top Wire'),
        ('N#3 Ultrasonic  Bottom', 'N#3 Ultrasonic  Bottom'),
        ('N#3 Ultrasonic Top', 'N#3 Ultrasonic Top'),
        ('N#5 ALU Bottom', 'N#5 ALU Bottom'),
        ('N#5 ALU Top Wire', 'N#5 ALU Top Wire'),
        ('N#5 PIN AND BOX', 'N#5 PIN AND BOX'),
        ('N#5 Ultrasonic Bottom', 'N#5 Ultrasonic Bottom'),
        ('N#5 Ultrasonic Top', 'N#5 Ultrasonic Top'),
        ('Others Item', 'Others Item'),
        ('P#3 Polyester tape', 'P#3 Polyester tape'),
        ('P#3 Special Slider', 'P#3 Special Slider'),
        ('P#5 Polyester GRS', 'P#5 Polyester GRS'),
        ('P#5 Polyester Tape', 'P#5 Polyester Tape'),
        ('P#5 Special Slider', 'P#5 Special Slider'),
        ('P#5 STD Slider', 'P#5 STD Slider'),
        ('Paint & Chemical', 'Paint & Chemical'),
        ('Resin', 'Resin'),
        ('Scrap', 'Scrap')
    ],string='PUR Description', store=False, readonly=False, copy=True)
    #description_purchase = fields.Text('Purchase Description', related='pur_description', translate=True)
    
    @api.onchange('pur_description')
    def onchange_pur_description(self):
        self.description_purchase = ''
        if self.pur_description !="":
            self.description_purchase = self.pur_description