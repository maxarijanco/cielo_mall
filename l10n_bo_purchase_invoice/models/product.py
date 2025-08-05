# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = ['product.template']
    
    
    global_discount = fields.Boolean(
        string='Descuento global',
        copy=False
    )
    