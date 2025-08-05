# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime
import calendar
import logging

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class HrDiasTrabajados(models.Model):
    _name = 'hr.dias.trabajados'
    _description = 'Dias trabajados Mes'

    def _mes_actual(self):
        return datetime.now().strftime('%m')

    MESES = [
        ('01', 'ENERO'),
        ('02', 'FEBRERO'),
        ('03', 'MARZO'),
        ('04', 'ABRIL'),
        ('05', 'MAYO'),
        ('06', 'JUNIO'),
        ('07', 'JULIO'),
        ('08', 'AGOSTO'),
        ('09', 'SEPTIEMBRE'),
        ('10', 'OCTUBRE'),
        ('11', 'NOVIEMBRE'),
        ('12', 'DICIEMBRE'),
    ]

    mes = fields.Selection(MESES, string='Mes planilla', default=_mes_actual, copy=False)
    anio = fields.Selection([(str(year), str(year)) for year in range(2018, 2030)], 'Año', copy=False)
    state = fields.Selection([('borrador', 'Borrador'), ('activo', 'Activado'), ('inactivo', 'Inactivo')], string='Estado', default='borrador')
    compania = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    detalle_planilla = fields.One2many('hr.dias.trabajados.detalle', 'detalle_id', string='Detalle Empleados')

    def action_generar_empleados(self):
        _logger.info(self)

class HrPlanillaEmpleadosIva(models.Model):
    _name = 'hr.dias.trabajados.detalle'
    _description = 'Detalle de dias trabajados Empleados'

    detalle_id = fields.Many2one('hr.dias.trabajados')
    empleado = fields.Many2one('hr.employee')
    dias_trabajados = fields.Integer(string='Dias Trabajados', default=30)
    nota = fields.Text(string='Notas')
    compania = fields.Many2one('res.company', string='Company', related='detalle_id.compania')

class Meses(models.Model):
    _name = 'mes.mes'
    _description = 'Meses del año'

    codigo = fields.Integer(string='Codigo')
    name = fields.Char(string='Nombre')

class HrEmpleadosRetroactivos(models.Model):
    _name = 'hr.retroactivos'
    _description = 'Retroactivos'

    def _mes_actual(self):
        return datetime.now().strftime('%m')

    MESES = [
        ('01', 'ENERO'),
        ('02', 'FEBRERO'),
        ('03', 'MARZO'),
        ('04', 'ABRIL'),
        ('05', 'MAYO'),
        ('06', 'JUNIO'),
        ('07', 'JULIO'),
        ('08', 'AGOSTO'),
        ('09', 'SEPTIEMBRE'),
        ('10', 'OCTUBRE'),
        ('11', 'NOVIEMBRE'),
        ('12', 'DICIEMBRE'),
    ]

    meses = fields.Many2many('mes.mes', 'retroactivo_mes_rel', 'retroactivo_id', 'mes_id', string='Meses', required=True)
    porcentaje = fields.Float(string="Porcentaje")
    departamentos = fields.Many2many('hr.department', 'retroactivo_dep_rel', 'department_id', 'depart_id')
    anio = fields.Selection([(str(year), str(year)) for year in range(2018, 2026)], 'Año', copy=False)
    state = fields.Selection([('borrador', 'Borrador'), ('activo', 'Activado'), ('inactivo', 'Inactivo')], string='Estado', default='borrador')
    compania = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    detalle_planilla = fields.One2many('hr.retroactivos.detalle', 'detalle_id', string='Detalle Empleados')

    def action_generar_empleados(self):
        _logger.info(self)

    @api.onchange('porcentaje')
    def porcentaje_retroactivo(self):
        for line in self:
            for l in line.detalle_planilla:
                l.porcentaje = line.porcentaje

class HrEmpleadosRetroactivosDetalle(models.Model):
    _name = 'hr.retroactivos.detalle'
    _description = 'Detalle de retroactivos Empleados'

    detalle_id = fields.Many2one('hr.retroactivos')
    empleado = fields.Many2one('hr.employee')
    porcentaje = fields.Float(string='Porcentaje')
    nota = fields.Text(string='Notas')
    compania = fields.Many2one('res.company', string='Company', related='detalle_id.compania')
