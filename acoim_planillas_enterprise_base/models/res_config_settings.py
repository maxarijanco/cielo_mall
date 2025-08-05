# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    haber_basico = fields.Float(string='Haber básico')

class IncrementoSalarial(models.Model):
    _name = 'hr.incremento.salarial'
    _rec_name = 'fecha_promulgacion'
    _order = 'fecha_promulgacion desc'
    _description = 'Incremento de Sueldos y Salarios'

    fecha_promulgacion = fields.Date(string='Fecha de Promulgación', required=True)
    decreto_supremo = fields.Char(string='Decreto Supremo')
    aumento_salario_basico = fields.Float(string='Aumento al Salario Básico (%)')
    empleados_beneficiados = fields.Many2many('hr.employee', 'salario_empleados_rel', 'incremento_id', 'empleado_id', string='Empleados Beneficiados', help='Empleados que perciben el incremento')

    @api.model
    def create(self, vals):
        year = datetime.strptime(vals.get('fecha_promulgacion'), "%Y-%m-%d").year
        existing_increment = self.search([('fecha_promulgacion', '>=', f'{year}-01-01'), ('fecha_promulgacion', '<=', f'{year}-12-31')])
        if existing_increment:
            raise UserError(_("El año del incremento salarial que trata de crear ya existe.\nSolo se permite un registro de incremento por año."))
        return super(IncrementoSalarial, self).create(vals)

class HrSalarioBasico(models.Model):
    _name = 'hr.salario.basico'
    _description = 'Salario Básico'
    _rec_name = 'fecha'

    monto = fields.Float(string='Salario básico')
    fecha = fields.Date(string='Fecha')

class HrBonoAntiguedad(models.Model):
    _name = 'hr.bono.antiguedad'
    _description = 'Bono Antigüedad'
    _rec_name = 'monto'

    monto = fields.Float(string='Monto %')
    anio_inicial = fields.Integer(string='Año inicial')
    anio_final = fields.Integer(string='Año final')

class HrAporteNacionalSolidario(models.Model):
    _name = 'hr.aporte.nacional.solidario'
    _description = 'Aporte Nacional Solidario'
    _rec_name = 'name'

    name = fields.Char(string='Nombre')
    operador = fields.Selection([('<', '<'), ('<=', '<='), ('=', '='), ('>=', '>='), ('>', '>')], string='Operador')
    total_ganado = fields.Float(string='Total Ganado')
    monto_inicial = fields.Float(string='Monto Inicial')
    monto_final = fields.Float(string='Monto Final')
    porcentaje_aporte = fields.Float(string='% Aplicativo', help='% Para obtener el Aporte Nacional Solidario')
