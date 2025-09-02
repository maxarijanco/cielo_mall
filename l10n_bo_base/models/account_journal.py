# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountJournal(models.Model):
    _inherit = ['account.journal']
    
    bo_edi = fields.Boolean(
        string='Factura (BO)',
        copy=False,
        help='Activar diario para movimientos fiscales (BO)'   
    )