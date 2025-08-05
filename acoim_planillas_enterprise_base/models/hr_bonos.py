# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class HrBono(models.Model):
    _name = 'hr.bono'
    _description='Bono'


    bono = fields.Many2one('hr.tipo.bono',string='Tipo bono')
    modo_bono = fields.Selection([('Porcentual','Porcentual'),('Monetario','Monetario')], 'Modo Bono', required=True, copy=False)
    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha_bono = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id

class HrTipoBono(models.Model):
    _name = 'hr.tipo.bono'
    _description='Tipo Bono'

    name = fields.Char(string="Nombre")
    modo_bono = fields.Selection([('Porcentual','Porcentual'),('Monetario','Monetario')], 'Modo Bono', required=True, copy=False)
    monto = fields.Float(string='Monto')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)


class HrAnticipoSueldos(models.Model):
    _name = 'hr.anticipos'
    _description='anticipos'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id
