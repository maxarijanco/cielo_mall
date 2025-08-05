# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta, date
import json
import io
from odoo.tools import date_utils
import calendar
import base64
from odoo.exceptions import AccessError, UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class HrPlanillaIva(models.Model):
    _name = 'hr.planilla.iva'
    _rec_name = 'payslip'
    _description='Planilla de RC-IVA'

    def _mes_actual(self):
        mes = datetime.now().month
        return f'{mes:02d}'

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
    anio = fields.Selection([('2018','2018'),('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),('2025','2025')], 'Año', copy=False)
    state = fields.Selection([('borrador','Borrador'),('activo','Activado'),('inactivo','Inactivo')], string='Estado', default='borrador')
    compania = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    detalle_planilla = fields.One2many('hr.planilla.empleado.iva', 'planilla_id', string='Detalle Planilla RC-IVA')
    payslip = fields.Many2one('hr.payslip.run', string='Planilla')
    ufv_inicial = fields.Char(string='UVF inicial')
    ufv_final = fields.Char(string='UVF final')

    @api.onchange('payslip')
    def cambio_moneda(self):
        if self.payslip:
            moneda = self.env['res.currency'].search([('name','=','UFV'),('active','=',True)])
            if moneda:
                anio = (self.payslip.date_start).year
                mes = str((self.payslip.date_start).month)

                if int(mes) == 1:
                    mes_anterior = 12
                    anio = anio - 1
                else:
                    mes_anterior = f'{int(mes)-1:02d}'

                dias_mes = calendar.monthrange(anio, int(mes_anterior))
                fin_mes = f'{anio}-{mes_anterior}-{dias_mes[1]}'
                cambio_ini = self.env['res.currency.rate'].search([('name','=',fin_mes),('currency_id','=',moneda.id),('company_id','=',self.compania.id)])
                if cambio_ini:
                    self.ufv_inicial = cambio_ini.rate
                else:
                    raise UserError(_("El año o mes correspondiente no cuenta con una moneda de cambio para la fecha "+str(fin_mes)+". \n Por favor registre un cambio en UFV correspondiente a la fecha"))
   
                cambio_fin = self.env['res.currency.rate'].search([('name','=',str(self.payslip.date_end)),('currency_id','=',moneda.id),('company_id','=',self.compania.id)])
                if cambio_fin:
                    self.ufv_final = cambio_fin.rate
                else:
                    raise UserError(_("El año o mes correspondiente no cuenta con una moneda de cambio para la fecha "+str(self.payslip.date_end)+". \n Por favor registre un cambio en UFV correspondiente a la fecha"))

    def action_generar_planilla_iva(self):
        _logger.info(self)

    def generar_planilla_rciva(self):
        _logger.info(self)

    def generar_planilla_rciva_csv(self):
        _logger.info(self)

class HrPlanillaEmpleadosIva(models.Model):
    _name = 'hr.planilla.empleado.iva'
    _description = 'Detalle de Planilla RC-IVA'

    planilla_id = fields.Many2one('hr.planilla.iva')
    anio = fields.Char('Año')
    empleado = fields.Many2one('hr.employee')
    periodo = fields.Char(string='Periodo')
    documento_dependiente = fields.Char(string='Codigo Dependiente RC-IVA')
    nombres = fields.Char(string='Nombres')
    primer_apellido = fields.Char(string='Primer Apellido')
    segundo_apellido = fields.Char(string='Segundo Apellido')
    documento = fields.Char(string='Documento de Documento Identidad')
    tipo_documento = fields.Many2one('hr.tipo.documento.identidad', string='tipo Documento')
    novedades = fields.Selection([('Incorporacion','Incorporacion'),('Vigente','Vigente'),('Desvinculado','Desvinculado')], string='Novedades')
    monto_ingreso = fields.Char(string='Monto de Ingreso Neto')
    salarios_minimos = fields.Char(string='Dos(2) Salarios Minimos Nacionales')
    importe_sujeto = fields.Char(string='Importe Sujeto a Impuesto (Base Imponible)')
    rc_iva = fields.Char(string='Impuesto RC-IVA')
    rc_iva_salarios_minimos = fields.Char(string='13% de Dos(2) Salarios Minimos Nacionales')
    impuesto_neto_rc_iva = fields.Char(string='Impuesto neto RC-IVA')
    total_facturas = fields.Char(string='F-110 \n Casilla 693')
    saldo_fisco = fields.Char(string='Saldo a Favor del Fisco')
    saldo_favor_dependiente = fields.Char(string='Saldo a Favor del Dependiente')
    saldo_periodo_anterior = fields.Char(string='Saldo a Favor del Dependiente Periodo Anterior')
    mantenimiento_periodo_anterior = fields.Char(string='Mantenimiento Saldo Periodo Anterior')
    saldo_periodo_anterior_actualizado = fields.Char(string='Saldo del Periodo Anterior Actualizado')
    saldo_utilizado = fields.Char(string='Saldo Utilizado')
    saldo_sujeto_retencion = fields.Char(string='Saldo RC-IVA sujeto a retencion')
    pago_acuenta_periodo_anterior = fields.Char(string='Pago a cuenta SIETE-RG Periodo Anterior')
    facturas_retenciones = fields.Char(string='F-110 \n Casilla 465')
    total_facturas_retenciones = fields.Char(string='Total saldo pago a cuenta SIETE-RG utilizado')
    retenciones_saldo_utilizado = fields.Char(string='Pago a cuenta SIETE-RG utilizado')
    impuesto_rc_iva_retenido = fields.Char(string='Impuesto RC-IVA Retenido')
    saldo_siguiente_mes = fields.Char(string='Saldo de Credito Fiscal a Favor del Dependiente para el Mes Siguiente')
    saldo_retencion_siguiente_mes = fields.Char(string='Saldo de pago a cuenta SIETE-RG a Favor del Dependiente para el Mes Siguiente')
