# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class HrAsignacionHorasExtra(models.Model):
    _name = 'hr.asignacion.horas.extra'
    _description='Hora Extra'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha_asignada = fields.Date(string='Fecha')
    numero_horas = fields.Float(string='Numero Horas')
    valor = fields.Float(string='Valor')
    modo = fields.Selection([('Nocturno','Nocturno'),('Extra','Extra')], 'Modo Bono', required=True, copy=False)
    nota = fields.Text(string='Nota')


    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id

    @api.onchange('valor', 'numero_horas', 'modo')
    def _onchange_calculo_horas_extra(self):
        def salario_basico(fecha,compania):
            cadena = str(fecha).split('-')
            self.env.cr.execute("SELECT monto FROM hr_salario_basico WHERE date_part('year',fecha) = '"+str(cadena[0])+"' ORDER BY id DESC LIMIT 1")
            valor = [i[0] for i in self.env.cr.fetchall()]
            minimo = 0
            if len(valor)>0:
                return valor[0]
            else:
                raise UserError(_("El año correspondiente al registro, no cuenta con un salario basico. \n Por favor registre un salario minimo para el año correspondiente"))
        for line in self:
            calculo_horas = 0
            if line.fecha_asignada:
                salario_minimo = self.employee.contract_id.wage
                _logger.info(salario_minimo)
                if line.numero_horas:
                    if line.modo == "Extra":
                        calculo_horas =  (salario_minimo / 240) * line.numero_horas * 2
                    elif line.modo == "Nocturno":
                        calculo_horas =  (salario_minimo / 240) * line.numero_horas * (30/100)
                line.valor = calculo_horas


class HrHorasExtra(models.Model):
    _name = 'hr.horas.extra'
    _description='Hora Extra'

    name = fields.Char(string="Nombre")
    fecha_asignada = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)


class HrAsignacionFacturasPresentadas(models.Model):
    _name = 'hr.asignacion.facturas.presentadas'
    _description='Hora Extra'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')


    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id

class HrAsignacionSaldoFavorDependiente(models.Model):
    _name = 'hr.asignacion.saldo.favor.dependiente'
    _description='Saldo A favor Dependiente Periodo Anterior'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id


class HrAsignacionFacturasRetencion(models.Model):
    _name = 'hr.asignacion.facturas.retencion'
    _description='Hora Extra'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto %')
    nota = fields.Text(string='Nota')

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id

class HrAsignacionSaldoFavorRetencion(models.Model):
    _name = 'hr.asignacion.saldo.favor.retencion'
    _description='Saldo A favor Dependiente Periodo Anterior Retencion'

    employee = fields.Many2one('hr.employee',string='Empleado')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.user.company_id)
    fecha = fields.Date(string='Fecha')
    monto = fields.Float(string='Monto')
    nota = fields.Text(string='Nota')

    @api.onchange('employee')
    def _onchange_empleado(self):
        if self.employee:
            self.company_id= self.employee.company_id.id