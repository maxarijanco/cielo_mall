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
from odoo.exceptions import AccessError, UserError, ValidationError
import xlsxwriter
import datetime
from pytz import timezone
import pytz
from io import BytesIO

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes
import logging
_logger = logging.getLogger(__name__)

class HrPlanillaIva(models.Model):
    _inherit = 'hr.planilla.iva'

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.onchange('payslip')
    def cambio_moneda(self):
        if self.payslip:
            self.compania= self.payslip.company_id.id
            moneda = self.env['res.currency'].search([('name','=','UFV'),('active','=',True)])
            if moneda:
                anio = (self.payslip.date_start).year
                mes = str((self.payslip.date_start).month)

                if int(mes)==1:
                    mes_anterior=12
                    anio = anio-1
                else:
                    if len(mes)<2:
                        mes = '0' + str(int(mes)-1)
                    else:
                        mes = str(int(mes)-1)
                        if len(mes)<2:
                            mes = '0' + str(int(mes))
                            _logger.info(mes)
                    mes_anterior = mes
                dias_mes = calendar.monthrange(anio,int(mes_anterior))
                fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
                cambio_ini = self.env['res.currency.rate'].search([('name','=',str(fin_mes)),('currency_id','=',moneda.id),('company_id','=',self.compania.id)])
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
        def salario_basico(fecha,compania):
            cadena = str(fecha).split('-')
            self.env.cr.execute("SELECT monto FROM hr_salario_basico WHERE date_part('year',fecha) = '"+str(cadena[0])+"' ORDER BY id DESC LIMIT 1")
            valor = [i[0] for i in self.env.cr.fetchall()]
            minimo = 0
            if len(valor)>0:
                return valor[0]
            else:
                raise UserError(_("El año El año correspondiente al registro, no cuenta con un salario basico. \n Por favor registre un salario minimo para el año correspondiente"))
        
        planilla = self.env['hr.planilla'].search([('payslip','=',self.payslip.id),('state','=','activo')])
        planilla_empleado = self.env['hr.planilla.empleado'].search([('planilla_id','=',planilla.id)])
        salario_minimo = salario_basico(self.payslip.date_end,self.compania.id)
        self.env.cr.execute("DELETE FROM hr_planilla_empleado_iva WHERE planilla_id="+str(self.id))
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip.id)])
        for pay in payslips:
            salario_minimo = total_ganado = total_facturas = rc_iva = aporte_nacional = aporte_laboral = facturas_retenciones = 0.00
            salario_minimo = pay.salario_minimo
            total_facturas = (pay.facturas_presentadas)
            facturas_retenciones = (pay.facturas_retenciones)
            cadena_nombre = pay.employee_id.name.split(' ')
            nombres = primer_apellido = segundo_apellido = ''
            codigo_dependiente = pay.employee_id.codigo_rc_iva
            documento = ''
            if pay.employee_id.identification_id:
                documento = str(pay.employee_id.identification_id).split(' ')
                documento=documento[0]
            tipo = pay.employee_id.tipo.id
            novedad = pay.employee_id.novedades
            if len(cadena_nombre)>0:
                if pay.employee_id.doble_nombre:
                    if len(cadena_nombre)==1:
                        nombres = str(cadena_nombre[0])
                    if len(cadena_nombre)==2:
                        nombres = str(cadena_nombre[0]) + " " + str(cadena_nombre[1])
                    if len(cadena_nombre)>2 and len(cadena_nombre)==3:
                        nombres = str(cadena_nombre[0]) + " " + str(cadena_nombre[1])
                        primer_apellido = str(cadena_nombre[2] or ' ')
                    if len(cadena_nombre)==4:
                        nombres = str(cadena_nombre[0]) + " " + str(cadena_nombre[1])
                        primer_apellido = str(cadena_nombre[2] or ' ')
                        segundo_apellido = str(cadena_nombre[3] or ' ')
                else:
                    if len(cadena_nombre)==1:
                        nombres = str(cadena_nombre[0])
                    if len(cadena_nombre)==2:
                        nombres = str(cadena_nombre[0])
                        primer_apellido = str(cadena_nombre[1] or ' ')
                    if len(cadena_nombre)==3:
                        nombres = str(cadena_nombre[0])
                        primer_apellido = str(cadena_nombre[1] or ' ')
                        segundo_apellido = str(cadena_nombre[2] or ' ')

            for slips in pay.line_ids:
                if slips.code == 'GROSS':
                    total_ganado = slips.amount
                if slips.code == 'AFPAL':
                    aporte_laboral = slips.amount
                if slips.code == 'AFPASN':
                    aporte_nacional = slips.amount
            importe_sujeto = neto = 0.00
            neto = total_ganado -(aporte_nacional+aporte_laboral)
            if float(neto)>float((salario_minimo*2)):
                importe_sujeto = float(neto) - float((salario_minimo*2))
            impuesto_rciva = 0.00
            if importe_sujeto>0:
                impuesto_rciva = float(importe_sujeto)*float(13/100)
            trece_salario_minimo = 0.00
            if salario_minimo>0 and importe_sujeto>0:
                trece_salario_minimo = float((salario_minimo*2))*float(13/100)
            impuesto_neto_rciva = 0.00
            if float(impuesto_rciva)>float(trece_salario_minimo):
                impuesto_neto_rciva = round(impuesto_rciva)-round(trece_salario_minimo)
            facturas_presentadas = total_facturas
            saldo_favor_fisco = 0.00
            if float(impuesto_neto_rciva)>float(facturas_presentadas):
                saldo_favor_fisco = float(impuesto_neto_rciva)-float(facturas_presentadas)
            saldo_favor_dependiente = 0.00
            if float(impuesto_neto_rciva)<float(facturas_presentadas):
                saldo_favor_dependiente = float(facturas_presentadas)-float(impuesto_neto_rciva)
            _logger.info(saldo_favor_dependiente)
            saldo_favor_dependiente_ant = 0.00
            saldo_favor_retencion_ant = 0.00
            anio = (pay.date_from).year
            mes = str((pay.date_from).month)

            if int(mes)==1:
                mes_anterior=12
                anio = anio-1
            else:
                if len(mes)<2:
                    mes = '0' + str(int(mes)-1)
                else:
                    mes = str(int(mes)-1)
                    if len(mes)<2:
                        mes = '0' + str(int(mes))
                        _logger.info(mes)
                mes_anterior = mes
            dias_mes = calendar.monthrange(anio,int(mes_anterior))
            inicio_mes = str(anio) + '-' + str(mes_anterior) + '-' + '01'
            fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
            
            def saldo_favor_dependiente_calculo(empleado,fecha_inicial,fecha_final,compania):
                anio = (fecha_inicial).year
                mes = str((fecha_inicial).month)
                if int(mes)==1:
                    mes_anterior=12
                    anio = anio-1
                else:
                    if len(mes)<2:
                        mes = '0' + str(int(mes)-1)
                    else:
                        mes = str(int(mes)-1)
                        if len(mes)<2:
                            mes = '0' + str(int(mes))
                            _logger.info(mes)
                    mes_anterior = mes
                dias_mes = calendar.monthrange(anio,int(mes_anterior))
                inicio_mes = str(anio) + '-' + str(mes_anterior) + '-' + str('01')
                fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
                self.env.cr.execute("SELECT SUM(monto) FROM hr_asignacion_saldo_favor_dependiente where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(inicio_mes)+"' AND '"+str(fin_mes)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                saldo = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return saldo

            def saldo_favor_dependiente_retenciones(empleado,fecha_inicial,fecha_final,compania):
                anio = (fecha_inicial).year
                mes = str((fecha_inicial).month)

                if int(mes)==1:
                    mes_anterior=12
                    anio = anio-1
                else:
                    if len(mes)<2:
                        mes = '0' + str(int(mes)-1)
                    else:
                        mes = str(int(mes)-1)
                        if len(mes)<2:
                            mes = '0' + str(int(mes))
                            _logger.info(mes)
                    mes_anterior = mes
                dias_mes = calendar.monthrange(anio,int(mes_anterior))
                inicio_mes = str(anio) + '-' + str(mes_anterior) + '-' + str('01')
                fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
                _logger.info(inicio_mes)
                _logger.info(fin_mes)
                self.env.cr.execute("SELECT SUM(monto) FROM hr_asignacion_saldo_favor_retencion where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(inicio_mes)+"' AND '"+str(fin_mes)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                saldo = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return saldo

            _logger.info(saldo_favor_dependiente)
            registro = self.env['hr.payslip'].search([('employee_id','=',pay.employee_id.id),('date_from','=',str(inicio_mes)),('date_to','=',str(fin_mes))])
            if registro:
                planilla_iva = self.env['hr.planilla.iva'].search([('payslip','=',registro.payslip_run_id.id)])
                planilla_iva_detalle = self.env['hr.planilla.empleado.iva'].search([('planilla_id','=',planilla_iva.id),('empleado','=',pay.employee_id.id)])
                if planilla_iva_detalle:
                    saldo_favor_dependiente_ant = float(planilla_iva_detalle.saldo_siguiente_mes)
                    saldo_favor_retencion_ant = float(planilla_iva_detalle.saldo_retencion_siguiente_mes)
            else:
                saldo_favor_dependiente_ant = saldo_favor_dependiente_calculo(pay.employee_id.id,pay.date_from,pay.date_to,pay.company_id.id)
                saldo_favor_retencion_ant = saldo_favor_dependiente_retenciones(pay.employee_id.id,pay.date_from,pay.date_to,pay.company_id.id)

            mantenimiento_saldo_favor = 0.00
            mantenimiento_saldo_favor = round(saldo_favor_dependiente_ant)*((float(self.ufv_inicial)/float(self.ufv_final))-1)
            if float(mantenimiento_saldo_favor)<0:
                mantenimiento_saldo_favor = 0.00
            saldo_periodo_anterior_actualizado = 0.00
            saldo_periodo_anterior_actualizado = round(mantenimiento_saldo_favor)+round(saldo_favor_dependiente_ant)
            saldo_utilizado = 0.00
            if round(saldo_periodo_anterior_actualizado)>round(saldo_favor_fisco):
                saldo_utilizado = round(saldo_favor_fisco)
            if round(saldo_periodo_anterior_actualizado)<round(saldo_favor_fisco):
                saldo_utilizado = round(saldo_periodo_anterior_actualizado)
            saldo_sujeto_retencion = 0.00
            if float(saldo_favor_fisco)> float(saldo_utilizado):
                saldo_sujeto_retencion = float(saldo_favor_fisco)- float(saldo_utilizado)
            impuesto_rc_iva_retenido = 0.00
            if float(saldo_favor_fisco)>float(saldo_utilizado):
                impuesto_rc_iva_retenido = float(saldo_favor_fisco) - float(saldo_utilizado)
            saldo_favor_mes_siguiente = 0.00
            total_facturas_retenciones = 0.00
            total_facturas_retenciones = float(saldo_favor_retencion_ant)+float(facturas_retenciones)
            retenciones_saldo_utilizado = 0.00
            if float(saldo_sujeto_retencion)>=float(total_facturas_retenciones):
                retenciones_saldo_utilizado = total_facturas_retenciones
            if float(saldo_sujeto_retencion)<float(total_facturas_retenciones):
                retenciones_saldo_utilizado = saldo_sujeto_retencion
            saldo_favor_mes_siguiente = float(saldo_favor_dependiente)+ float(saldo_periodo_anterior_actualizado)-float(saldo_utilizado)
            _logger.info(saldo_favor_mes_siguiente)
            saldo_retencion_siguiente_mes = 0.00
            saldo_retencion_siguiente_mes = float(total_facturas_retenciones) + float(retenciones_saldo_utilizado)
            self.env['hr.planilla.empleado.iva'].create({
                'planilla_id':self.id,
                'anio':self.payslip.date_start.year,
                'empleado':pay.employee_id.id,
                'periodo':self.payslip.date_start.month,
                'documento_dependiente':codigo_dependiente,
                'nombres':nombres,
                'primer_apellido':primer_apellido,
                'segundo_apellido':segundo_apellido,
                'documento':documento,
                'tipo_documento':tipo,
                'novedades':novedad,
                'monto_ingreso':round(float(neto),2),
                'salarios_minimos':(salario_minimo*2),
                'importe_sujeto':round(importe_sujeto,2),
                'rc_iva':round(impuesto_rciva,2),
                'rc_iva_salarios_minimos':round(trece_salario_minimo,2),
                'impuesto_neto_rc_iva':round(impuesto_neto_rciva,2),
                'total_facturas':round(facturas_presentadas,2),
                'saldo_fisco':round(saldo_favor_fisco,2),
                'saldo_favor_dependiente':round(saldo_favor_dependiente,2),
                'saldo_periodo_anterior':round(saldo_favor_dependiente_ant,2),
                'mantenimiento_periodo_anterior':round(mantenimiento_saldo_favor,2),
                'saldo_periodo_anterior_actualizado':round(saldo_periodo_anterior_actualizado,2),
                'saldo_utilizado':round(saldo_utilizado,2),
                'saldo_sujeto_retencion':round(saldo_sujeto_retencion,2),
                'pago_acuenta_periodo_anterior':round(saldo_favor_retencion_ant,2),
                'facturas_retenciones':round(facturas_retenciones,2),
                'total_facturas_retenciones':round(total_facturas_retenciones,2),
                'retenciones_saldo_utilizado':round(retenciones_saldo_utilizado,2),
                'impuesto_rc_iva_retenido':round(impuesto_rc_iva_retenido,2),
                'saldo_siguiente_mes':round(saldo_favor_mes_siguiente,2),
                'saldo_retencion_siguiente_mes':round(saldo_retencion_siguiente_mes,2),
                })

        self.state='activo'


    def _prepare_report_data(self):
        data = {
            'compania': self.compania.id,
            'run': self.payslip.id,
            'id': self.id,
        }
        return data

    def generar_planilla_rciva(self):
        self.ensure_one()
        data = self._prepare_report_data()
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)
        workbook.close()
        fout=encodebytes(file_io.getvalue())
        
        datetime_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Planilla RC-IVA'
        filename = '%s_%s'%(report_name,datetime_string)
        self.write({'fileout':fout, 'fileout_filename':filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=fileout&download=true&filename='+filename,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        titulo1 = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo1_border = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow', 'border': True})
        titulo2 = workbook.add_format({'font_size': 12, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo3 = workbook.add_format({'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo4 = workbook.add_format({'font_size': 12, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})

        cabecera1 = workbook.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': True, 'bold': True, 'font_name': 'Arial Narrow'})

        valor_formato1 = workbook.add_format({'font_size': 8, 'align': 'left',   'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True})
        valor_formato2 = workbook.add_format({'font_size': 8, 'align': 'center', 'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True})
        valor_formato3 = workbook.add_format({'font_size': 8, 'align': 'right',  'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'num_format': '#,##0.00'})

        total_formato1 = workbook.add_format({'font_size': 10, 'align': 'left',   'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True})
        total_formato2 = workbook.add_format({'font_size': 10, 'align': 'center', 'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True})
        total_formato3 = workbook.add_format({'font_size': 10, 'align': 'right',  'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True, 'num_format': '#,##0.00'})
        #Alto de la fila
        sheet = workbook.add_worksheet('Reporte de Planilla')
        sheet.set_row(6,40) #Posición, tamaño, formato de celda, opciones

        #Margenes
        sheet.set_column('A:A', 2) 
        sheet.set_column('B:B', 10) 
        sheet.set_column('C:C', 25) 
        sheet.set_column('D:D', 10) 
        sheet.set_column('E:E', 13) 
        sheet.set_column('F:F', 13) 
        sheet.set_column('G:G', 13) 
        sheet.set_column('H:H', 15) 
        sheet.set_column('I:I', 15) 
        sheet.set_column('J:J', 15) 
        sheet.set_column('K:K', 15) 
        sheet.set_column('L:L', 12) 
        sheet.set_column('M:M', 12) 
        sheet.set_column('N:N', 11) 
        sheet.set_column('O:O', 11) 
        sheet.set_column('P:P', 11) 
        sheet.set_column('Q:Q', 11) 
        sheet.set_column('R:R', 11) 
        sheet.set_column('S:S', 11) 
        sheet.set_column('T:T', 11) 
        sheet.set_column('U:U', 11) 
        sheet.set_column('V:V', 11) 
        sheet.set_column('W:W', 11) 
        sheet.set_column('X:X', 11) 
        sheet.set_column('Y:Y', 11) 
        sheet.set_column('Z:Z', 11) 
        sheet.set_column('AA:AA', 11) 
        sheet.set_column('AB:AB', 11) 
        sheet.set_column('AC:AC', 11) 
        sheet.set_column('AD:AD', 11) 
        sheet.set_column('AE:AE', 11) 

        #Titulos
        sheet.merge_range('A1:C1', 'NOMBRE O RAZON SOCIAL:', titulo2)
        sheet.merge_range('D1:F1', self.compania.name, titulo4)
        sheet.merge_range('A2:C2', 'DIRECCION:', titulo2)
        sheet.merge_range('D2:F2', self.compania.street, titulo4)
        sheet.merge_range('A3:C3', 'N° NIT:', titulo2)
        sheet.merge_range('D3:F3', self.compania.vat, titulo4)          
        sheet.merge_range('A4:C4', 'N° EMPLEADOR (CAJA DE SALUD)  CPS:   ', titulo2)
        sheet.merge_range('D4:F4', self.compania.nro_salud, titulo4)
        sheet.merge_range('A5:C5', 'N° EMPLEADOR MINISTERIO DE TRABAJO:', titulo2)
        sheet.merge_range('D5:F5', self.compania.nro_ministerio, titulo4)
        sheet.merge_range('A6:C6', 'REPRESENTANTE LEGAL:', titulo2)
        sheet.merge_range('D6:F6', self.compania.responsable_legal, titulo4)
        sheet.merge_range('A7:C7', 'N° C.I. REPRESENTANTE LEGAL', titulo2)
        sheet.merge_range('D7:F7', self.compania.ci_responsable_legal, titulo4)
        sheet.merge_range('A8:C8', 'DIRECCION:', titulo2)
        sheet.merge_range('D8:F8', self.compania.street2, titulo4)
        sheet.merge_range('A9:C9', 'TELEFONO:', titulo2)
        sheet.merge_range('D9:F9', self.compania.phone, titulo4)
        sheet.merge_range('A10:C10', 'CORREO:', titulo2)
        sheet.merge_range('D10:F10', self.compania.email, titulo4)
        payslips_run = self.env['hr.payslip.run'].search([('id','=',data['run'])])
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',data['run'])])
        def _mes_actual(fecha):
            if fecha.month == 1: return 'ENERO'
            if fecha.month == 2: return 'FEBRERO'
            if fecha.month == 3: return 'MARZO'
            if fecha.month == 4: return 'ABRIL'
            if fecha.month == 5: return 'MAYO'
            if fecha.month == 6: return 'JUNIO'
            if fecha.month == 7: return 'JULIO'
            if fecha.month == 8: return 'AGOSTO'
            if fecha.month == 9: return 'SEPTIEMBRE'
            if fecha.month == 10: return 'OCTUBRE'
            if fecha.month == 11: return 'NOVIEMBRE'
            if fecha.month == 12: return 'DICIEMBRE'
        mes = _mes_actual(payslips_run.date_end)
        sheet.merge_range('A12:Y12', 'PLANILLA TRIBUTARIA', titulo3)
        sheet.merge_range('A13:Y13', 'CORRESPONDIENTE AL MES DE '+str(mes)+' DEL AÑO '+str(payslips_run.date_end.year), titulo3)
        sheet.merge_range('A14:Y14', '( Expresado en Bolivianos )', titulo3)
        # sheet.merge_range('A15:Y15', '( Expresado en Bolivianos )', titulo3)
        sheet.merge_range('A17:A18', 'Nº', cabecera1)
        sheet.merge_range('B17:B18', 'AÑO', cabecera1)
        sheet.merge_range('C17:C18', 'PERIODO', cabecera1)
        sheet.merge_range('D17:D18', 'CODIGO DEPENDIENTE RC-IVA', cabecera1)
        sheet.merge_range('E17:E18', 'NOMBRES', cabecera1)
        sheet.merge_range('F17:F18', 'PRIMER APELLIDO', cabecera1)
        sheet.merge_range('G17:G18', 'SEGUNDO APELLIDO', cabecera1)
        sheet.merge_range('H17:H18', 'NUMERO DE DOCUMENTO IDENTIDAD', cabecera1)
        sheet.merge_range('I17:I18', 'TIPO DE DOCUMENTO', cabecera1)
        sheet.merge_range('J17:J18', 'NOVEDADES (I=INCORPORACION V=VIGENTE D=DESVINCULADO)', cabecera1)
        sheet.merge_range('K17:K18', 'MONTO DE INGRESO NETO', cabecera1)
        sheet.merge_range('L17:L18', 'DOS (2) SMN NO IMPONIBLES', cabecera1)
        sheet.merge_range('M17:M18', 'IMPORTE SUJETO A IMPUESTO(BASE IMPONIBLE)', cabecera1)
        sheet.merge_range('N17:N18', 'IMPUESTO RC-IVA', cabecera1)
        sheet.merge_range('O17:O18', '13% DE DOS (2) SMN', cabecera1)
        sheet.merge_range('P17:P18', 'IMPUESTO NETO RC-IVA', cabecera1)
        sheet.merge_range('Q17:Q18', 'F-110 \n CASILLA 693', cabecera1)
        sheet.merge_range('R17:R18', 'SALDO A FAVOR DEL FISCO', cabecera1)
        sheet.merge_range('S17:S18', 'SALDO A FAVOR DEL DEPENDIENTE', cabecera1)
        sheet.merge_range('T17:T18', '"SALDO A FAVOR DEL DEPENDIENTE DEL PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('U17:U18', 'MANTENIMIENTO DE VALOR DEL SALDO A FAVOR \n DEL DEPENDIENTE DEL PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('V17:V18', 'SALDO DEL PERIODO ANTERIOR UTILIZADO', cabecera1)
        sheet.merge_range('W17:W18', 'SALDO UTILIZADO', cabecera1)
        sheet.merge_range('X17:X18', 'SALDO RC-IVA SUJETO A RETENCION', cabecera1)
        sheet.merge_range('Y17:Y18', 'PAGO A CUENTA SIETE-RG PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('Z17:Z18', 'F-110 \n CASILLA 465', cabecera1)
        sheet.merge_range('AA17:AA18', 'TOTAL  SALDO  PAGO A CUENTA \n SIETE-RG DEL PERIODO', cabecera1)
        sheet.merge_range('AB17:AB18', 'PAGO A CUENTA \n SIETE-RG UTILIZADO', cabecera1)
        sheet.merge_range('AC17:AC18', 'IMPUESTO RC-IVA RETENIDO', cabecera1)
        sheet.merge_range('AD17:AD18', 'SALDO DE CREDITO FISCAL A FAVOR DEL DEPENDIENTE PARA EL MES SIGUIENTE', cabecera1)
        sheet.merge_range('AE17:AE18', 'SALDO DE PAGO A CUENTA SIETE-RG A FAVOR DEL DEPENDIENTE PARA EL MES SIGUIENTE', cabecera1)
        filas=17
        numero = 0
        iva = self.env['hr.planilla.iva'].search([('id','=',data['id'])])
        detalle_planilla = 0
        for consulta in iva.detalle_planilla:
            tipo_documento=''
            if consulta.tipo_documento:
                tipo_documento = consulta.tipo_documento.code
            filas+=1
            numero+=1
            sheet.write(filas, 0, numero, valor_formato1)
            sheet.write(filas, 1, consulta.anio, valor_formato2) 
            sheet.write(filas, 2, consulta.periodo, valor_formato1) 
            sheet.write(filas, 3, consulta.documento_dependiente, valor_formato1) 
            sheet.write(filas, 4, consulta.nombres, valor_formato1) 
            sheet.write(filas, 5, consulta.primer_apellido, valor_formato1) 
            sheet.write(filas, 6, consulta.segundo_apellido, valor_formato1) 
            sheet.write(filas, 7, consulta.documento, valor_formato1) 
            sheet.write(filas, 8, tipo_documento, valor_formato1) 
            sheet.write(filas, 9, consulta.novedades[0], valor_formato1) 
            sheet.write(filas, 10, consulta.monto_ingreso, valor_formato1) 
            sheet.write(filas, 11, consulta.salarios_minimos, valor_formato1) 
            sheet.write(filas, 12, consulta.importe_sujeto, valor_formato1) 
            sheet.write(filas, 13, consulta.rc_iva, valor_formato1) 
            sheet.write(filas, 14, consulta.rc_iva_salarios_minimos, valor_formato1) 
            sheet.write(filas, 15, consulta.impuesto_neto_rc_iva, valor_formato1) 
            sheet.write(filas, 16, consulta.total_facturas, valor_formato1) 
            sheet.write(filas, 17, consulta.saldo_fisco, valor_formato1) 
            sheet.write(filas, 18, consulta.saldo_favor_dependiente, valor_formato1) 
            sheet.write(filas, 19, consulta.saldo_periodo_anterior, valor_formato1) 
            sheet.write(filas, 20, consulta.mantenimiento_periodo_anterior, valor_formato1) 
            sheet.write(filas, 21, consulta.saldo_periodo_anterior_actualizado, valor_formato1) 
            sheet.write(filas, 22, consulta.saldo_utilizado, valor_formato1) 
            sheet.write(filas, 23, consulta.saldo_sujeto_retencion, valor_formato1) 
            sheet.write(filas, 24, consulta.pago_acuenta_periodo_anterior, valor_formato1) 
            sheet.write(filas, 25, consulta.facturas_retenciones, valor_formato1) 
            sheet.write(filas, 26, consulta.total_facturas_retenciones, valor_formato1) 
            sheet.write(filas, 27, consulta.retenciones_saldo_utilizado, valor_formato1) 
            sheet.write(filas, 28, consulta.impuesto_rc_iva_retenido, valor_formato1)
            sheet.write(filas, 29, consulta.saldo_siguiente_mes, valor_formato1)
            sheet.write(filas, 30, consulta.saldo_retencion_siguiente_mes, valor_formato1) 

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Reporte de Planilla')
        #Estilos
        titulo1 = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo1_border = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow', 'border': True})
        titulo2 = workbook.add_format({'font_size': 12, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo3 = workbook.add_format({'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})
        titulo4 = workbook.add_format({'font_size': 12, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'font_name': 'Arial Narrow'})

        cabecera1 = workbook.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': True, 'bold': True, 'font_name': 'Arial Narrow'})

        valor_formato1 = workbook.add_format({'font_size': 8, 'align': 'left',   'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True})
        valor_formato2 = workbook.add_format({'font_size': 8, 'align': 'center', 'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True})
        valor_formato3 = workbook.add_format({'font_size': 8, 'align': 'right',  'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'num_format': '#,##0.00'})

        total_formato1 = workbook.add_format({'font_size': 10, 'align': 'left',   'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True})
        total_formato2 = workbook.add_format({'font_size': 10, 'align': 'center', 'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True})
        total_formato3 = workbook.add_format({'font_size': 10, 'align': 'right',  'font_name': 'Arial Narrow', 'text_wrap': True, 'valign': 'top', 'border': True, 'bold': True, 'num_format': '#,##0.00'})
        #Alto de la fila
        sheet.set_row(6,40) #Posición, tamaño, formato de celda, opciones

        #Margenes
        sheet.set_column('A:A', 2) 
        sheet.set_column('B:B', 10) 
        sheet.set_column('C:C', 25) 
        sheet.set_column('D:D', 10) 
        sheet.set_column('E:E', 13) 
        sheet.set_column('F:F', 13) 
        sheet.set_column('G:G', 13) 
        sheet.set_column('H:H', 15) 
        sheet.set_column('I:I', 15) 
        sheet.set_column('J:J', 15) 
        sheet.set_column('K:K', 15) 
        sheet.set_column('L:L', 12) 
        sheet.set_column('M:M', 12) 
        sheet.set_column('N:N', 11) 
        sheet.set_column('O:O', 11) 
        sheet.set_column('P:P', 11) 
        sheet.set_column('Q:Q', 11) 
        sheet.set_column('R:R', 11) 
        sheet.set_column('S:S', 11) 
        sheet.set_column('T:T', 11) 
        sheet.set_column('U:U', 11) 
        sheet.set_column('V:V', 11) 
        sheet.set_column('W:W', 11) 
        sheet.set_column('X:X', 11) 
        sheet.set_column('Y:Y', 11) 
        sheet.set_column('Z:Z', 11) 
        sheet.set_column('AA:AA', 11) 
        sheet.set_column('AB:AB', 11) 
        sheet.set_column('AC:AC', 11) 
        sheet.set_column('AD:AD', 11) 
        sheet.set_column('AE:AE', 11) 

        #Titulos
        sheet.merge_range('A1:C1', 'NOMBRE O RAZON SOCIAL:', titulo2)
        sheet.merge_range('D1:F1', self.compania.razon_social, titulo4)
        sheet.merge_range('A2:C2', 'DIRECCION:', titulo2)
        sheet.merge_range('D2:F2', self.compania.street, titulo4)
        sheet.merge_range('A3:C3', 'N° NIT:', titulo2)
        sheet.merge_range('D3:F3', self.compania.vat, titulo4)          
        sheet.merge_range('A4:C4', 'N° EMPLEADOR (CAJA DE SALUD)  CPS:   ', titulo2)
        sheet.merge_range('D4:F4', self.compania.nro_salud, titulo4)
        sheet.merge_range('A5:C5', 'N° EMPLEADOR MINISTERIO DE TRABAJO:', titulo2)
        sheet.merge_range('D5:F5', self.compania.nro_ministerio, titulo4)
        sheet.merge_range('A6:C6', 'REPRESENTANTE LEGAL:', titulo2)
        sheet.merge_range('D6:F6', self.compania.responsable_legal, titulo4)
        sheet.merge_range('A7:C7', 'N° C.I. REPRESENTANTE LEGAL', titulo2)
        sheet.merge_range('D7:F7', self.compania.ci_responsable_legal, titulo4)
        sheet.merge_range('A8:C8', 'DIRECCION:', titulo2)
        sheet.merge_range('D8:F8', self.compania.street2, titulo4)
        sheet.merge_range('A9:C9', 'TELEFONO:', titulo2)
        sheet.merge_range('D9:F9', self.compania.phone, titulo4)
        sheet.merge_range('A10:C10', 'CORREO:', titulo2)
        sheet.merge_range('D10:F10', self.compania.email, titulo4)
        payslips_run = self.env['hr.payslip.run'].search([('id','=',data['run'])])
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',data['run'])])
        def _mes_actual(fecha):
            if fecha.month == 1: return 'ENERO'
            if fecha.month == 2: return 'FEBRERO'
            if fecha.month == 3: return 'MARZO'
            if fecha.month == 4: return 'ABRIL'
            if fecha.month == 5: return 'MAYO'
            if fecha.month == 6: return 'JUNIO'
            if fecha.month == 7: return 'JULIO'
            if fecha.month == 8: return 'AGOSTO'
            if fecha.month == 9: return 'SEPTIEMBRE'
            if fecha.month == 10: return 'OCTUBRE'
            if fecha.month == 11: return 'NOVIEMBRE'
            if fecha.month == 12: return 'DICIEMBRE'
        mes = _mes_actual(payslips_run.date_end)
        sheet.merge_range('A12:Y12', 'PLANILLA TRIBUTARIA', titulo3)
        sheet.merge_range('A13:Y13', 'CORRESPONDIENTE AL MES DE '+str(mes)+' DEL AÑO '+str(payslips_run.date_end.year), titulo3)
        sheet.merge_range('A14:Y14', '( Expresado en Bolivianos )', titulo3)
        # sheet.merge_range('A15:Y15', '( Expresado en Bolivianos )', titulo3)
        sheet.merge_range('A17:A18', 'Nº', cabecera1)
        sheet.merge_range('B17:B18', 'AÑO', cabecera1)
        sheet.merge_range('C17:C18', 'PERIODO', cabecera1)
        sheet.merge_range('D17:D18', 'CODIGO DEPENDIENTE RC-IVA', cabecera1)
        sheet.merge_range('E17:E18', 'NOMBRES', cabecera1)
        sheet.merge_range('F17:F18', 'PRIMER APELLIDO', cabecera1)
        sheet.merge_range('G17:G18', 'SEGUNDO APELLIDO', cabecera1)
        sheet.merge_range('H17:H18', 'NUMERO DE DOCUMENTO IDENTIDAD', cabecera1)
        sheet.merge_range('I17:I18', 'TIPO DE DOCUMENTO', cabecera1)
        sheet.merge_range('J17:J18', 'NOVEDADES (I=INCORPORACION V=VIGENTE D=DESVINCULADO)', cabecera1)
        sheet.merge_range('K17:K18', 'MONTO DE INGRESO NETO', cabecera1)
        sheet.merge_range('L17:L18', 'DOS (2) SMN NO IMPONIBLES', cabecera1)
        sheet.merge_range('M17:M18', 'IMPORTE SUJETO A IMPUESTO(BASE IMPONIBLE)', cabecera1)
        sheet.merge_range('N17:N18', 'IMPUESTO RC-IVA', cabecera1)
        sheet.merge_range('O17:O18', '13% DE DOS (2) SMN', cabecera1)
        sheet.merge_range('P17:P18', 'IMPUESTO NETO RC-IVA', cabecera1)
        sheet.merge_range('Q17:Q18', 'F-110 \n CASILLA 693', cabecera1)
        sheet.merge_range('R17:R18', 'SALDO A FAVOR DEL FISCO', cabecera1)
        sheet.merge_range('S17:S18', 'SALDO A FAVOR DEL DEPENDIENTE', cabecera1)
        sheet.merge_range('T17:T18', '"SALDO A FAVOR DEL DEPENDIENTE DEL PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('U17:U18', 'MANTENIMIENTO DE VALOR DEL SALDO A FAVOR \n DEL DEPENDIENTE DEL PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('V17:V18', 'SALDO DEL PERIODO ANTERIOR UTILIZADO', cabecera1)
        sheet.merge_range('W17:W18', 'SALDO UTILIZADO', cabecera1)
        sheet.merge_range('X17:X18', 'SALDO RC-IVA SUJETO A RETENCION', cabecera1)
        sheet.merge_range('Y17:Y18', 'PAGO A CUENTA SIETE-RG PERIODO ANTERIOR', cabecera1)
        sheet.merge_range('Z17:Z18', 'F-110 \n CASILLA 465', cabecera1)
        sheet.merge_range('AA17:AA18', 'TOTAL  SALDO  PAGO A CUENTA \n SIETE-RG DEL PERIODO', cabecera1)
        sheet.merge_range('AB17:AB18', 'PAGO A CUENTA \n SIETE-RG UTILIZADO', cabecera1)
        sheet.merge_range('AC17:AC18', 'IMPUESTO RC-IVA RETENIDO', cabecera1)
        sheet.merge_range('AD17:AD18', 'SALDO DE CREDITO FISCAL A FAVOR DEL DEPENDIENTE PARA EL MES SIGUIENTE', cabecera1)
        sheet.merge_range('AE17:AE18', 'SALDO DE PAGO A CUENTA SIETE-RG A FAVOR DEL DEPENDIENTE PARA EL MES SIGUIENTE', cabecera1)
        filas=17
        numero = 0
        iva = self.env['hr.planilla.iva'].search([('id','=',data['id'])])
        detalle_planilla = 0
        for consulta in iva.detalle_planilla:
            tipo_documento=''
            if consulta.tipo_documento:
                tipo_documento = consulta.tipo_documento.code
            filas+=1
            numero+=1
            sheet.write(filas, 0, numero, valor_formato1)
            sheet.write(filas, 1, consulta.anio, valor_formato2) 
            sheet.write(filas, 2, consulta.periodo, valor_formato1) 
            sheet.write(filas, 3, consulta.documento_dependiente, valor_formato1) 
            sheet.write(filas, 4, consulta.nombres, valor_formato1) 
            sheet.write(filas, 5, consulta.primer_apellido, valor_formato1) 
            sheet.write(filas, 6, consulta.segundo_apellido, valor_formato1) 
            sheet.write(filas, 7, consulta.documento, valor_formato1) 
            sheet.write(filas, 8, tipo_documento, valor_formato1) 
            sheet.write(filas, 9, consulta.novedades[0], valor_formato1) 
            sheet.write(filas, 10, consulta.monto_ingreso, valor_formato1) 
            sheet.write(filas, 11, consulta.salarios_minimos, valor_formato1) 
            sheet.write(filas, 12, consulta.importe_sujeto, valor_formato1) 
            sheet.write(filas, 13, consulta.rc_iva, valor_formato1) 
            sheet.write(filas, 14, consulta.rc_iva_salarios_minimos, valor_formato1) 
            sheet.write(filas, 15, consulta.impuesto_neto_rc_iva, valor_formato1) 
            sheet.write(filas, 16, consulta.total_facturas, valor_formato1) 
            sheet.write(filas, 17, consulta.saldo_fisco, valor_formato1) 
            sheet.write(filas, 18, consulta.saldo_favor_dependiente, valor_formato1) 
            sheet.write(filas, 19, consulta.saldo_periodo_anterior, valor_formato1) 
            sheet.write(filas, 20, consulta.mantenimiento_periodo_anterior, valor_formato1) 
            sheet.write(filas, 21, consulta.saldo_periodo_anterior_actualizado, valor_formato1) 
            sheet.write(filas, 22, consulta.saldo_utilizado, valor_formato1) 
            sheet.write(filas, 23, consulta.saldo_sujeto_retencion, valor_formato1) 
            sheet.write(filas, 24, consulta.pago_acuenta_periodo_anterior, valor_formato1) 
            sheet.write(filas, 25, consulta.facturas_retenciones, valor_formato1) 
            sheet.write(filas, 26, consulta.total_facturas_retenciones, valor_formato1) 
            sheet.write(filas, 27, consulta.retenciones_saldo_utilizado, valor_formato1) 
            sheet.write(filas, 28, consulta.impuesto_rc_iva_retenido, valor_formato1)
            sheet.write(filas, 29, consulta.saldo_siguiente_mes, valor_formato1)
            sheet.write(filas, 30, consulta.saldo_retencion_siguiente_mes, valor_formato1) 


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    
    import base64

    def generar_planilla_rciva_csv(self):
        aumentar = ""
        saltopagina = "\r\n"
        numero = 0
        iva = self.env['hr.planilla.iva'].search([('id', '=', self.id)])
        detalle_planilla = 0
        _logger.info(self)
        
        # Función interna para obtener el nombre del mes
        def _mes_actual(fecha):
            meses = [
                'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
            ]
            return meses[fecha.month - 1]

        # Obtener mes en formato correcto para el nombre del archivo
        mes = str(self.payslip.date_end.month)
        if len(mes) < 2:
            mes = '0' + str(int(mes))
        filename = 'PLA_' + str(self.compania.vat) + "_" + str(self.payslip.date_end.year) + "_" + str(mes) + ".csv"

        # Construcción del contenido del CSV
        for consulta in self.detalle_planilla:
            tipo_documento = consulta.tipo_documento.code if consulta.tipo_documento else ''
            _logger.info(str(round(float(consulta.monto_ingreso))))
            
            aumentar += (
                f"{consulta.anio};{consulta.periodo};{consulta.documento_dependiente};"
                f"{consulta.nombres};{consulta.primer_apellido};{consulta.segundo_apellido};"
                f"{consulta.documento};{tipo_documento};{consulta.novedades[0]};"
                f"{round(float(consulta.monto_ingreso))};{round(float(consulta.salarios_minimos))};"
                f"{round(float(consulta.importe_sujeto))};{round(float(consulta.rc_iva))};"
                f"{round(float(consulta.rc_iva_salarios_minimos))};{round(float(consulta.impuesto_neto_rc_iva))};"
                f"{round(float(consulta.total_facturas))};{round(float(consulta.saldo_fisco))};"
                f"{round(float(consulta.saldo_favor_dependiente))};{round(float(consulta.saldo_periodo_anterior))};"
                f"{round(float(consulta.mantenimiento_periodo_anterior))};"
                f"{round(float(consulta.saldo_periodo_anterior_actualizado))};"
                f"{round(float(consulta.saldo_utilizado))};{round(float(consulta.saldo_sujeto_retencion))};"
                f"{round(float(consulta.pago_acuenta_periodo_anterior))};{round(float(consulta.facturas_retenciones))};"
                f"{round(float(consulta.total_facturas_retenciones))};{round(float(consulta.retenciones_saldo_utilizado))};"
                f"{round(float(consulta.impuesto_rc_iva_retenido))};{round(float(consulta.saldo_siguiente_mes))};"
                f"{round(float(consulta.saldo_retencion_siguiente_mes))}{saltopagina}"
            )

        # Contenido final del archivo TXT
        txt_planilla_csv = aumentar

        # Usar ir.attachment para guardar el archivo como adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(txt_planilla_csv.encode()).decode('utf-8'),
            'res_model': self._name,  # Relacionar el adjunto con el modelo actual
            'res_id': self.id,
            'mimetype': 'text/csv'
        })

        # Retornar el adjunto creado para ser descargado
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

