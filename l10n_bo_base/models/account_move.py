# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountMove(models.Model):
    _inherit = ['account.move']
    
    # ------------------------------------------------------------------------------

    invoice_number = fields.Float(
        string='Nro. Factura',
        copy=False, 
        digits=(20, 0)
    )

    # ------------------------------------------------------------------------------
    
    cuf = fields.Char(
        string='CUF',
        help='Codigo unico de facturación.',
        copy=False,
    )

    # ------------------------------------------------------------------------------
    