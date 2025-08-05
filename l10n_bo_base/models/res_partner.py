# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = ['res.partner']
    

    
    complement = fields.Char(
        string='Complemento',
        copy=False
    )