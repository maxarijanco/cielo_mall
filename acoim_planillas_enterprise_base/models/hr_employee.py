# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    fecha_ingreso = fields.Date(string='Fecha Ingreso')
    fecha_retiro = fields.Date(string='Fecha Retiro',invisible=True)
    salario = fields.Float(string='Salario',invisible=True)
    doble_nombre = fields.Boolean(string='Doble Nombre')
    jubilado = fields.Boolean(string='¿Es Jubilado?',default=False)
    aporte_afp = fields.Boolean(string='¿Decide aportar AFP?',default=False)
    descuentos = fields.One2many('hr.descuentos','employee',string="Descuentos",invisible=True)
    total_descuentos = fields.Float(string='Descuentos')
    codigo_rc_iva = fields.Char(string='Codigo Dependiente RC-IVA')
    tipo = fields.Many2one('hr.tipo.documento.identidad',string='Tipo documento')
    novedades = fields.Selection([('Incorporacion','Incorporacion'),('Vigente','Vigente'),('Desvinculado','Desvinculado')], string='Novedades',default='Vigente')
    codigo_css = fields.Char(string='Codigo Caja seguro Social')

class hrTipoDocumentoIdentidad(models.Model):
    _name = "hr.tipo.documento.identidad"
    _description="Tipo Documento Identidad"

    name = fields.Char(string='Nombre')
    code = fields.Char(string='Codigo')