# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta, date
import json
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from odoo.tools import date_utils
import calendar
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import base64
import logging
_logger = logging.getLogger(__name__)

class HrPlanilla(models.Model):
    _name = 'hr.planilla'
    _rec_name = 'payslip'
    _description='Planilla de Sueldos y Salarios'

    def _mes_actual(self):
        if datetime.now().month == 1: return '01'
        if datetime.now().month == 2: return '02'
        if datetime.now().month == 3: return '03'
        if datetime.now().month == 4: return '04'
        if datetime.now().month == 5: return '05'
        if datetime.now().month == 6: return '06'
        if datetime.now().month == 7: return '07'
        if datetime.now().month == 8: return '08'
        if datetime.now().month == 9: return '09'
        if datetime.now().month == 10: return '10'
        if datetime.now().month == 11: return '11'
        if datetime.now().month == 12: return '12'

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
    anio = fields.Selection([('2018','2018'),('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),('2025','2025')], string='Año')
    state = fields.Selection([('borrador','Borrador'),('activo','Activado'),('inactivo','Inactivo')], string='Estado', default='borrador')
    compania = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    detalle_planilla = fields.One2many('hr.planilla.empleado', 'planilla_id', string='Detalle Planilla')
    payslip = fields.Many2one('hr.payslip.run',string='Planilla')

    def action_generar_planilla(self):
        _logger.info(self)

    def generar_planilla(self):
        _logger.info(self)

    def generar_planilla_csv(self):
        _logger.info(self)


class HrPlanillaEmpleados(models.Model):
    _name = 'hr.planilla.empleado'
    _description = 'Detalle de planilla de Sueldos y Salarios'

    planilla_id = fields.Many2one('hr.planilla')
    empleado = fields.Many2one('hr.employee')
    numero = fields.Char(string='N°')
    documento = fields.Char(string='Documento de identidad')
    nombres = fields.Char(string='Nombre o Razon Social')
    pais = fields.Char(string='Nacionalidad')
    sexo = fields.Char(string='Sexo(V/M)')
    cargo = fields.Char(string='Cargo')
    fecha_ingreso = fields.Char(string='Fecha de ingreso')
    dias_pagados = fields.Char(string='Días pagados (Mes)')
    haber_basico = fields.Char(string='Haber básico')
    incremento_salarial = fields.Char(string='Incremento Salarial')
    horas_pagadas = fields.Char(string='Horas pagadas (Día)')
    bono_antiguedad = fields.Char(string='Bono de Antigüedad')
    bono_produccion = fields.Char(string='Bono de producción')
    numero_horas = fields.Char(string='Numero Horas')
    monto_pagado = fields.Char(string='Monto Pagado')
    pago_dominical = fields.Char(string='Pago dominical y domingo trabajado')
    otros_bonos = fields.Char(string='Otros bonos')
    total_ganado = fields.Char(string='Total Ganado')
    sistema_integral = fields.Char(string='SIP 12,71')
    aporte_nacional = fields.Char(string='A.N.S.')
    rc_iva = fields.Char(string='RC-IVA 13%')
    otros_descuentos = fields.Char(string='Otros descuentos')
    anticipos = fields.Char(string='Anticipos')
    total_descuentos = fields.Char(string='Total descuentos')
    liquido_pagable = fields.Char(string='Liquido Pagable')

class HrPlanillaRetroactivo(models.Model):
    _name = 'hr.retroactivo.empleados'
#     _rec_name = 'payslip_retro'
    _description='Planilla de Retroactivos'

    def _mes_actual(self):
        if datetime.now().month == 1: return '01'
        if datetime.now().month == 2: return '02'
        if datetime.now().month == 3: return '03'
        if datetime.now().month == 4: return '04'
        if datetime.now().month == 5: return '05'
        if datetime.now().month == 6: return '06'
        if datetime.now().month == 7: return '07'
        if datetime.now().month == 8: return '08'
        if datetime.now().month == 9: return '09'
        if datetime.now().month == 10: return '10'
        if datetime.now().month == 11: return '11'
        if datetime.now().month == 12: return '12'

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
    anio = fields.Selection([('2018','2018'),('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),('2025','2025'),('2026','2026')], string='Año')
    state = fields.Selection([('borrador','Borrador'),('activo','Activado'),('inactivo','Inactivo')], string='Estado', default='borrador')
    compania = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    detalle_planilla = fields.One2many('hr.planilla.retroactivo', 'planilla_id', string='Detalle Planilla')
    payslip_retro = fields.Many2one('hr.payslip.run',string='Planilla',domain="[('retroactivo','=','True')]")

    def action_generar_planilla(self):
        _logger.info(self)

    def generar_planilla(self):
        _logger.info(self)

    def generar_planilla_csv(self):
        _logger.info(self)


class HrPlanillaEmpleadosRetro(models.Model):
    _name = 'hr.planilla.retroactivo'
    _description = 'Detalle de planilla de Retroactivos'

    planilla_id = fields.Many2one('hr.retroactivo.empleados')
    numero = fields.Char(string='N°')
    carnet = fields.Char(string='Carnet')
    empleado = fields.Many2one('hr.employee',string='empleado')
    genero = fields.Char(string='Sexo(V/M)')
    cargo = fields.Char(string='cargo')
    fecha_ingreso = fields.Char(string='Fecha de ingreso')
    haber_basico_ant = fields.Char(string='Haber Basico Anterior')
    haber_basico_inc = fields.Char(string='Haber Basico Incremento')
    bono_antiguedad_ant = fields.Char(string='Bono Antiguedad Anterior')
    bono_antiguedad_act = fields.Char(string='Bono Antiguedad Actual')
    enero_retro = fields.Char(string='Enero Retroactivo')
    bono_enero_retro = fields.Char(string='Bono Enero Retroactivo')
    febrero_retro = fields.Char(string='Febrero Retroactivo')
    bono_febrero_retro = fields.Char(string='Bono Febrero Retroactivo')
    marzo_retro = fields.Char(string='Marzo Retroactivo')
    bono_marzo_retro = fields.Char(string='Bono Marzo Retroactivo')
    abril_retro = fields.Char(string='Abril Retroactivo')
    bono_abril_retro = fields.Char(string='Bono Abril Retroactivo')
    mayo_retro = fields.Char(string='Mayo Retroactivo')
    bono_mayo_retro = fields.Char(string='Bono Mayo Retroactivo')
    total_retroactivo = fields.Char(string='Total Retroactivo')
    afp_retro = fields.Char(string='A.N.S.')
    rciva = fields.Char(string='RC-IVA 13%')
    otros_descuentos = fields.Char(string='Otros descuentos')
    total_descuentos = fields.Char(string='Total descuentos')
    liquido_pagable = fields.Char(string='Liquido Pagable')