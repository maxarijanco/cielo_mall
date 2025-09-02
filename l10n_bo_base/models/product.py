# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = ['product.template']
    
    
    global_discount = fields.Boolean(
        string='Es descuento Global',
        copy=False, 
        help='Habilitar para productos con descuento global'        
    )