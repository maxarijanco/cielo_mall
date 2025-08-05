# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    nro_salud = fields.Char(string='N° Empleador (Caja de Salud)  CPS')
    nro_ministerio = fields.Char(string='N° Empleador Ministerio de Trabajo')
    responsable_legal = fields.Char(string='Representante Legal')
    ci_responsable_legal = fields.Char(string='C.I. Responsable Legal')
    responsable_legal_partner = fields.Many2one('res.partner',string='Responsable Legal')
    
    @api.onchange('responsable_legal_partner')
    def onchangeName(self):
        if self.responsable_legal_partner:
            self.responsable_legal = self.responsable_legal_partner.razon_social