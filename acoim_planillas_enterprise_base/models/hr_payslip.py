# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta, date
from odoo.exceptions import AccessError, UserError, ValidationError  # Eliminado Warning
import json
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from odoo.tools import date_utils
import calendar
import logging
_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    total_descuentos_anticipos = fields.Monetary(string="Total Anticipos", compute='_compute_total_descuentos_anticipos')
    total_descuentos_multas = fields.Monetary(string="Total Multas", compute='_compute_total_descuentos_multas')

    horas_extra = fields.Float(string='Horas Extra', compute='_compute_values')
    incremento = fields.Float(string='Incremento Salarial', compute='_compute_values')
    bono_antiguedad = fields.Float(string='Bono Antiguedad', compute='_compute_values')
    bono_produccion = fields.Float(string='Bono Produccion')
    bono_dominical = fields.Float(string='Bono Dominical')
    otros_bonos = fields.Float(string='Otros Bonos', invisible=True)
    salario_minimo = fields.Float(string='Salario Minimo', compute='_compute_values')
    salario_minimo_act = fields.Float(string='Salario Minimo Actual', compute='_compute_values')
    total_descuentos = fields.Float(string='Total Descuentos', compute='_compute_values')
    total_bonos = fields.Float(string='Total Bonos', compute='_compute_values')
    total_anticipos = fields.Float(string='Total Anticipos', compute='_compute_values')
    facturas_presentadas = fields.Float(string='F-110 \n Casilla 693', compute='_compute_values')
    facturas_retenciones = fields.Float(string='F-110 \n Casilla 465', compute='_compute_values')
    saldo_favor_depend_ant = fields.Float(string='Saldo Favor dependiente', compute='_compute_values')
    saldo_favor_reten_ant = fields.Float(string='Saldo Favor retencion', compute='_compute_values')
    ufv_inicial = fields.Char(string='UVF inicial', compute='_compute_values')
    ufv_final = fields.Char(string='UVF final', compute='_compute_values')
    anios_empleado = fields.Integer(string='Años empleado', compute='_compute_values')
    jubilado = fields.Boolean(string='¿Es Jubilado?', default=False, compute='_compute_values')
    dias_trabajados = fields.Integer(string='Dias Trabajados', default=False, compute='_compute_values')
    porcentaje = fields.Float(string='Porcentaje Retroactivo', compute='_compute_retroactivo')
    retroactivo = fields.Boolean(string='Retroactivo', compute='_compute_retroactivo', store=True, readonly=False)
    retro_enero = fields.Many2one('hr.payslip', string='Retroactivo Enero', compute='_compute_retroactivo', store=True, readonly=False)
    retro_febrero = fields.Many2one('hr.payslip', string='Retroactivo Febrero', compute='_compute_retroactivo', store=True, readonly=False)
    retro_marzo = fields.Many2one('hr.payslip', string='Retroactivo Marzo', compute='_compute_retroactivo', store=True, readonly=False)
    retro_abril = fields.Many2one('hr.payslip', string='Retroactivo Abril', compute='_compute_retroactivo', store=True, readonly=False)
    retro_mayo = fields.Many2one('hr.payslip', string='Retroactivo Mayo', compute='_compute_retroactivo', store=True, readonly=False)

    def _compute_total_descuentos_anticipos(self):
        for payslip in self:
            descuentos = self.env['hr.descuentos'].search([('employee', '=', payslip.employee_id.id), ('fecha_descuento', '>=', payslip.date_from), ('fecha_descuento', '<=', payslip.date_to), ('tipo_descuento', '=', 'anticipo')])
            payslip.total_descuentos_anticipos = sum(descuento.monto for descuento in descuentos)

    def _compute_total_descuentos_multas(self):
        for payslip in self:
            descuentos = self.env['hr.descuentos'].search([('employee', '=', payslip.employee_id.id), ('fecha_descuento', '>=', payslip.date_from), ('fecha_descuento', '<=', payslip.date_to), ('tipo_descuento', '=', 'multa')])
            payslip.total_descuentos_multas = sum(descuento.monto for descuento in descuentos)

    

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_retroactivo(self):
        for line in self:
            porcentaje = 0
            line.porcentaje = porcentaje
            line.retroactivo = line.payslip_run_id.retroactivo
            line.retro_enero = False
            line.retro_febrero = False
            line.retro_marzo = False
            line.retro_abril = False
            line.retro_mayo = False

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_values(self):
        for line in self:
            descuento = bono = incremento = antiguedad = extra = salario_minimo = facturas = saldo_favor_dependiente_ant = retenciones = saldo_favor_retencion_ant = 0.00
            ufv_ini = ufv_fin = 0.00
            anticipo = 0.00
            anios_empl = 0
            dias_trabajados = 0
            empleado = False
            line.total_descuentos = descuento
            line.total_bonos = bono
            line.total_anticipos = anticipo
            line.incremento = incremento
            line.salario_minimo = salario_minimo
            line.salario_minimo_act = salario_minimo
            line.bono_antiguedad = antiguedad
            line.horas_extra = extra
            line.facturas_presentadas = facturas
            line.facturas_retenciones = retenciones
            line.saldo_favor_depend_ant = saldo_favor_dependiente_ant
            line.saldo_favor_reten_ant = saldo_favor_retencion_ant
            line.ufv_inicial = ufv_ini
            line.ufv_final = ufv_fin
            line.anios_empleado = anios_empl
            line.jubilado = empleado
            line.dias_trabajados = dias_trabajados

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    retroactivo = fields.Boolean(string='¿Es Retroactivo?', default=False)

    def generar_planilla(self):
        _logger.info(self)

    def generar_planilla_rciva(self):
        _logger.info(self)

