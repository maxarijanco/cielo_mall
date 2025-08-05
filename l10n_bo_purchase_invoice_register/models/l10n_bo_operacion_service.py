# -*- coding: utf-8 -*-

from odoo import api, models, fields

class L10nBoOperacionService(models.Model):
    _inherit = ['l10n.bo.operacion.service']
    
    
    service_type = fields.Selection(
        string = 'Tipo servicio',
        selection_add=[('ServicioRecepcionCompras', 'Registro de compras')]
    )
    