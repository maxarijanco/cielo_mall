# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class HrDiasTrabajados(models.Model):
    _inherit = 'hr.dias.trabajados'


    def action_generar_empleados(self):
        numero = 0
        empleados = self.env['hr.employee'].search([('company_id','=',self.compania.id),('active','=',True)])
        _logger.info(empleados)
        self.state='activo'
        self.env.cr.execute("DELETE FROM hr_dias_trabajados_detalle WHERE detalle_id="+str(self.id))
        for empl in empleados:
            self.env['hr.dias.trabajados.detalle'].create({
                'detalle_id':self.id,
                'empleado':empl.id,
                })

class HrEmpleadosretroactivo(models.Model):
    _inherit = 'hr.retroactivos'

    def action_generar_empleados(self):
        _logger.info(self)

        numero = 0

        self.state='activo'
        self.env.cr.execute("DELETE FROM hr_retroactivos_detalle WHERE detalle_id="+str(self.id))
        for dep in self.departamentos:
            empleados = self.env['hr.employee'].search([('department_id','=',dep.id),('company_id','=',self.compania.id),('active','=',True),('contract_id','!=',False)])
            _logger.info(empleados)
            for empl in empleados:
                self.env['hr.retroactivos.detalle'].create({
                    'detalle_id':self.id,
                    'empleado':empl.id,
                    })