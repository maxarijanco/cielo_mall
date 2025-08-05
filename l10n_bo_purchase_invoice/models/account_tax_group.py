# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountTaxGroup(models.Model):
    _inherit = ['account.tax.group']
    

    
    column_rc_type = fields.Selection(
        string='Tipo Columna RC',
        selection=[
            ('ice', 'RC ICE'), 
            ('iehd', 'RC IEHD'),
            ('ipj', 'RC IPJ'),
            ('rate', 'RC Tasas'),
            ('no_iva', 'RC no sujeto a C.F.'),
            ('exempt', 'RC Exentos'),
            ('cero_rate', 'RC Tasa cero'),
            ('dui_dim', 'RC IVA Importaciones (DUI/DIM)')
        ]
    )
    