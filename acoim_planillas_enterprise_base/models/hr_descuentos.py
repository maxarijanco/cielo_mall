# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class HrDescuentos(models.Model):
    _name = 'hr.descuentos'
    _description='Descuentos'

    tipo_descuento = fields.Many2one('hr.tipo.descuento',string='Tipo descuento')
    modo_descuento = fields.Selection([('Porcentual','Porcentual'),('Monetario','Monetario')], 'Modo descuento', required=True, copy=False)
    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha_descuento = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')

    @api.onchange('tipo_descuento')
    def recuperarvalores(self):
        if self.tipo_descuento:
            self.modo_descuento = self.tipo_descuento.modo_descuento
            self.monto = self.tipo_descuento.monto

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id

class HrTipoDescuentos(models.Model):
    _name = 'hr.tipo.descuento'
    _description='Tipo Descuentos'

    name = fields.Char(string="Nombre")
    modo_descuento = fields.Selection([('Porcentual','Porcentual'),('Monetario','Monetario')], 'Modo descuento', required=True, copy=False)
    monto = fields.Float(string='Monto')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)