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
import xlsxwriter
from pytz import timezone
import pytz
from io import BytesIO

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes
import logging
_logger = logging.getLogger(__name__)

class HrPlanilla(models.Model):
    _inherit = 'hr.planilla'

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.onchange('payslip')
    def cambio_moneda(self):
        _logger.info(self)
        # if self.payslip:
        #     self.compania= self.payslip.company_id.id

    def action_generar_planilla(self):
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip.id)])
        numero = 0
        self.state='activo'
        self.env.cr.execute("DELETE FROM hr_planilla_empleado WHERE planilla_id="+str(self.id))
        def horas_extras_realizadas(empleado,fecha_inicial,fecha_final,compania):
            self.env.cr.execute("SELECT SUM(numero_horas) FROM hr_asignacion_horas_extra where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha_asignada  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
            resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
            horas = 0
            if resultado_consulta[0] is not None:
                return resultado_consulta[0]
            else:
                return horas
        for pay in payslips:
            basico = incremento = horas_extra = bono_antiguedad = monto_pagado = bono_produccion = 0.00
            bono_dominical = otros_bonos = total_ganado = sip_patronal = sip_nacional = rc_iva = 0.00
            anticipo = total_descuento = liquido_pagable = 0.00
            extra = horas_extras_realizadas(pay.employee_id.id,pay.date_from,pay.date_to,pay.company_id.id)
            for slips in pay.line_ids:
                if slips.code == 'BASIC':
                    basico = slips.amount
                if slips.code == 'INCRE':
                    incremento = slips.amount
                if slips.code == 'BANTI':
                    bono_antiguedad = slips.amount
                if slips.code == 'BONOP':
                    bono_produccion = slips.amount
                if slips.code == 'HEXTR':
                    horas_extra = slips.amount
                if slips.code == 'BONOD':
                    bono_dominical = slips.amount
                if slips.code == 'OBONO':
                    otros_bonos = slips.amount
                if slips.code == 'GROSS':
                    total_ganado = slips.amount
                if slips.code == 'RCIVA':
                    rc_iva = slips.amount
                if slips.code == 'AFPASN':
                    sip_nacional = slips.amount
                if slips.code == 'AFPAL':
                    sip_patronal = slips.amount
                if slips.code == 'ANTIC':
                    anticipo = slips.amount
                if slips.code == 'TDESC':
                    total_descuento = slips.amount
                if slips.code == 'NETO':
                    liquido_pagable = slips.amount

            numero += 1
            genero = ''
            if pay.employee_id.gender == 'male':
                genero = 'M'
            if pay.employee_id.gender == 'female':
                genero = 'F'
            if pay.employee_id.gender == 'other':
                genero = 'O'
            self.env['hr.planilla.empleado'].create({
                'planilla_id':self.id,
                'empleado':pay.employee_id.id,
                'numero':numero,
                'documento':pay.employee_id.identification_id,
                'nombres':pay.employee_id.name,
                'pais':pay.employee_id.country_id.name,
                'sexo':genero,
                'cargo':pay.employee_id.job_title,
                'fecha_ingreso':(datetime.strptime(str(pay.employee_id.contract_id.date_start), '%Y-%m-%d')).strftime('%d/%m/%Y'),
                'dias_pagados':pay.dias_trabajados,
                'haber_basico':round(basico,2),
                'incremento_salarial':round(incremento,2),
                'horas_pagadas':'8',
                'bono_antiguedad':round(bono_antiguedad,2),
                'numero_horas':extra,
                'monto_pagado':horas_extra,
                'bono_produccion':round(bono_produccion,2),
                'pago_dominical':round(bono_dominical,2),
                'otros_bonos':round(otros_bonos,2),
                'total_ganado':round(total_ganado,2),
                'sistema_integral':round(sip_patronal,2),
                'aporte_nacional':round(sip_nacional,2),
                'rc_iva':round(rc_iva,2),
                'otros_descuentos':round(pay.total_descuentos,2),
                'anticipos':round(anticipo,2),
                'total_descuentos':round(total_descuento,2),
                'liquido_pagable':round(liquido_pagable,2),
                })

    def _prepare_report_data(self):
        data = {
            'compania': self.compania.id,
            'run': self.payslip.id,
        }
        return data

    def generar_planilla(self):
        self.ensure_one()
        data = self._prepare_report_data()
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)
        workbook.close()
        fout=encodebytes(file_io.getvalue())
        
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Planilla Sueldos y Salarios'
        filename = '%s_%s'%(report_name,datetime_string)
        self.write({'fileout':fout, 'fileout_filename':filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=fileout&download=true&filename='+filename,
        }

        # self.ensure_one()
        # self._compute_data()
        # return self.env.ref('acoim_planillas_enterprise_funcional.action_standard_excel_planilla').report_action(self)
        # if self.fecha_inicial > self.fecha_final:
        #     raise ValidationError('La fecha fecha_inicial no puede ser menor a la fecha final')
        # data = self._prepare_report_data()
        # return {
        #     'type': 'ir_actions_xlsx_download',
        #     'data': {'model': 'reporte.bancarizacion.wiz',
        #              'options': json.dumps(data, default=date_utils.json_default),
        #              'output_format': 'xlsx',
        #              'report_name': 'Bancarizacion',
        #              }
        # }
        # data = self._prepare_report_data()
        # return {
        #     'type': 'ir_actions_xlsx_download',
        #     'data': {'model': 'hr.planilla',
        #              'options': json.dumps(data, default=date_utils.json_default),
        #              'output_format': 'xlsx',
        #              'report_name': 'Planilla de Sueldos y Salarios',
        #              }
        # }
    def generate_xlsx_report(self, workbook, data=None, objs=None):


    # def get_xlsx_report(self, data, response):
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
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
        sheet.set_column('Y:Y', 20) 

        #Titulos
        compania = self.env['res.company'].search([('id','=',data['compania'])])
        sheet.merge_range('A1:C1', 'NOMBRE O RAZON SOCIAL:', titulo2)
        sheet.merge_range('D1:F1', compania.name, titulo4)
        sheet.merge_range('A2:C2', 'DIRECCION:', titulo2)
        sheet.merge_range('D2:F2', compania.street, titulo4)
        sheet.merge_range('A3:C3', 'N° NIT:', titulo2)
        sheet.merge_range('D3:F3', compania.vat, titulo4)          
        sheet.merge_range('A4:C4', 'N° EMPLEADOR (CAJA DE SALUD)  CPS:   ', titulo2)
        sheet.merge_range('D4:F4', compania.nro_salud, titulo4)
        sheet.merge_range('A5:C5', 'N° EMPLEADOR MINISTERIO DE TRABAJO:', titulo2)
        sheet.merge_range('D5:F5', compania.nro_ministerio, titulo4)
        sheet.merge_range('A6:C6', 'REPRESENTANTE LEGAL:', titulo2)
        sheet.merge_range('D6:F6', compania.responsable_legal, titulo4)
        sheet.merge_range('A7:C7', 'N° C.I. REPRESENTANTE LEGAL', titulo2)
        sheet.merge_range('D7:F7', compania.ci_responsable_legal, titulo4)
        sheet.merge_range('A8:C8', 'DIRECCION:', titulo2)
        sheet.merge_range('D8:F8', compania.street2, titulo4)
        sheet.merge_range('A9:C9', 'TELEFONO:', titulo2)
        sheet.merge_range('D9:F9', compania.phone, titulo4)
        sheet.merge_range('A10:C10', 'CORREO:', titulo2)
        sheet.merge_range('D10:F10', compania.email, titulo4)
        # cadena = "CORRESPONDIENTE AL MES DE" 
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
        sheet.merge_range('A12:Y12', 'PLANILLA DE SUELDOS Y SALARIOS', titulo3)
        sheet.merge_range('A13:Y13', 'CORRESPONDIENTE AL MES DE '+str(mes)+' DEL AÑO '+str(payslips_run.date_end.year), titulo3)
        sheet.merge_range('A14:Y14', 'PERSONAL PERMANENTE', titulo3)
        sheet.merge_range('A15:Y15', '( Expresado en Bolivianos )', titulo3)
        #Cabecera
        sheet.merge_range('A17:A18', 'Nº', cabecera1)
        sheet.merge_range('B17:B18', 'CARNET DE IDENTIDAD', cabecera1)
        sheet.merge_range('C17:C18', 'NOMBRE O RAZÓN SOCIAL', cabecera1)
        sheet.merge_range('D17:D18', 'NACIONALIDAD', cabecera1)
        sheet.merge_range('E17:E18', 'GENERO\n(F/M)', cabecera1)
        sheet.merge_range('F17:F18', 'CARGO', cabecera1)
        sheet.merge_range('G17:G18', 'FECHA \n INGRESO', cabecera1)
        sheet.merge_range('H17:H18', 'DIAS PAG. MES', cabecera1)
        sheet.merge_range('I17:I18', 'HABER BASICO', cabecera1)
        sheet.merge_range('J17:J18', 'INCREMENTO D.S. 3544', cabecera1)
        sheet.merge_range('K17:K18', 'HORAS POR DÍA PAG.', cabecera1)
        sheet.merge_range('L17:L18', 'BONO ANTIG.', cabecera1)
        sheet.merge_range('M17:N17', 'HORAS EXTRAS', cabecera1)
        sheet.write(17, 12, 'NUM', cabecera1)
        sheet.write(17, 13, 'MONTO PAGADO', cabecera1)
        sheet.merge_range('O17:O18', 'BONO DE PRODUCCION', cabecera1)
        sheet.merge_range('P17:P18', 'BONOS DOMINICAL', cabecera1)
        sheet.merge_range('Q17:Q18', 'OTROS BONOS', cabecera1)
        sheet.merge_range('R17:R18', 'TOTAL GANADO', cabecera1)
        sheet.merge_range('S17:V17', 'DESCUENTOS', cabecera1)
        sheet.write(17, 18, 'S.I.P. 12.71%', cabecera1)
        sheet.write(17, 19, 'A.N.S.', cabecera1)
        sheet.write(17, 20, 'RC-IVA 13%.', cabecera1)
        sheet.write(17, 21, 'ANTICIP OTROS DSCTOS.', cabecera1)
        sheet.merge_range('W17:W18', 'TOTAL DESCTOS.', cabecera1)
        sheet.merge_range('X17:X18', 'LIQUIDO PAGABLE', cabecera1)
        sheet.merge_range('Y17:Y18', 'FIRMA DEL \n EMPLEADO', cabecera1)
        numero = 0
        filas = 17
        thaber = tbono = tnumhoras = tmontohoras = tprodduccion = tdominical = totrosbonos = ttotalganado = tsipp = tsipn = trciva =tanticipos = tdescuentos = tliquido = 0 
        for pay in payslips:
            basico = incremento = horas_extra = bono_antiguedad = monto_pagado = bono_produccion = 0.00
            bono_dominical = otros_bonos = total_ganado = sip_patronal = sip_nacional = rc_iva = 0.00
            anticipo = total_descuento = liquido_pagable = 0.00
            for slips in pay.line_ids:
                if slips.code == 'BASIC':
                    basico = slips.amount
                if slips.code == 'INCRE':
                    incremento = slips.amount
                if slips.code == 'BANTI':
                    bono_antiguedad = slips.amount
                if slips.code == 'BONOP':
                    bono_produccion = slips.amount
                if slips.code == 'BONOD':
                    bono_dominical = slips.amount
                if slips.code == 'OBONO':
                    otros_bonos = slips.amount
                if slips.code == 'GROSS':
                    total_ganado = slips.amount
                if slips.code == 'RCIVA':
                    rc_iva = slips.amount
                if slips.code == 'AFPASN':
                    sip_nacional = slips.amount
                if slips.code == 'AFPAL':
                    sip_patronal = slips.amount
                if slips.code == 'ANTIC':
                    anticipo = slips.amount
                if slips.code == 'TDESC':
                    total_descuento = slips.amount
                if slips.code == 'NETO':
                    liquido_pagable = slips.amount

            numero += 1
            filas += 1
            genero = ''
            documento = ''
            if pay.employee_id.identification_id:
                documento = str(pay.employee_id.identification_id).split(' ')
            if pay.employee_id.gender == 'male':
                genero = 'M'
            if pay.employee_id.gender == 'female':
                genero = 'F'
            if pay.employee_id.gender == 'other':
                genero = 'O'
            sheet.write(filas, 0, numero, valor_formato1)
            sheet.write(filas, 1, str(documento[0]), valor_formato2) 
            sheet.write(filas, 2, pay.employee_id.name, valor_formato1) 
            sheet.write(filas, 3, pay.employee_id.country_id.name, valor_formato1) 
            sheet.write(filas, 4, genero, valor_formato1) 
            sheet.write(filas, 5, pay.employee_id.job_id.name, valor_formato1) 
            sheet.write(filas, 6, str(pay.employee_id.contract_id.date_start), valor_formato1) 
            sheet.write(filas, 7, pay.dias_trabajados, valor_formato1) 
            sheet.write(filas, 8, round(pay.employee_id.contract_id.wage,2), valor_formato1) 
            sheet.write(filas, 9, round(incremento,2), valor_formato1) 
            sheet.write(filas, 10, '8', valor_formato1) 
            sheet.write(filas, 11, round(bono_antiguedad,2), valor_formato1) 
            sheet.write(filas, 12, horas_extra, valor_formato1) 
            sheet.write(filas, 13, round(monto_pagado,2), valor_formato1) 
            sheet.write(filas, 14, round(bono_produccion,2), valor_formato1) 
            sheet.write(filas, 15, round(bono_dominical,2), valor_formato1) 
            sheet.write(filas, 16, round(otros_bonos,2), valor_formato1) 
            sheet.write(filas, 17, round(total_ganado,2), valor_formato1) 
            sheet.write(filas, 18, round(sip_patronal,2), valor_formato1) 
            sheet.write(filas, 19, round(sip_nacional,2), valor_formato1) 
            sheet.write(filas, 20, round(rc_iva,2), valor_formato1) 
            sheet.write(filas, 21, round(anticipo,2), valor_formato1) 
            sheet.write(filas, 22, round(total_descuento,2), valor_formato1) 
            sheet.write(filas, 23, round(liquido_pagable,2), valor_formato1)
            thaber += round(pay.employee_id.contract_id.wage,2)
            tbono +=round(bono_antiguedad,2)
            tnumhoras += horas_extra
            tmontohoras += round(monto_pagado,2)
            tprodduccion += round(bono_produccion,2)
            tdominical += round(bono_dominical,2)
            totrosbonos += round(otros_bonos,2)
            ttotalganado += round(total_ganado,2)
            tsipp += round(sip_patronal,2)
            tsipn += round(sip_nacional,2)
            trciva += round(rc_iva,2)
            tanticipos += round(anticipo,2)
            tdescuentos += round(total_descuento,2)
            tliquido += round(liquido_pagable,2)
        # # #Pie o Totales
        filas += 1
        # cadena = 'A' + str(filas+1) + ":"+'H' + str(filas+1)
        sheet.write(filas, 7, 'TOTALES', cabecera1)
        sheet.write(filas, 8, thaber, total_formato3)
        sheet.write(filas, 9, '', total_formato3)
        sheet.write(filas, 10, '', total_formato3)
        sheet.write(filas, 11, tbono, total_formato3)
        sheet.write(filas, 12, tnumhoras, total_formato3)
        sheet.write(filas, 13, tmontohoras, total_formato3)
        sheet.write(filas, 14, tprodduccion, total_formato3)
        sheet.write(filas, 15, tdominical, total_formato3)
        sheet.write(filas, 16, totrosbonos, total_formato3)
        sheet.write(filas, 17, ttotalganado, total_formato3)
        sheet.write(filas, 18, tsipp, total_formato3)
        sheet.write(filas, 19, tsipn, total_formato3)
        sheet.write(filas, 20, trciva, total_formato3)
        sheet.write(filas, 21, tanticipos, total_formato3)
        sheet.write(filas, 22, tdescuentos, total_formato3)
        sheet.write(filas, 23, tliquido, total_formato3)
        sheet.write(filas, 24, '', total_formato3)
        filas += 4
        sheet.write(filas, 7, compania.responsable_legal, titulo2)
        sheet.write(filas, 10, compania.ci_responsable_legal, titulo2)
        sheet.write(filas, 14, '__________________________', titulo2)
        filas += 1
        sheet.write(filas, 7, 'NOMBRE DEL EMPLEADOR O REPRESENTANTE LEGAL', titulo2)
        sheet.write(filas, 10, 'N° DE DOCUMENTO DE IDENTIDAD', titulo2)
        sheet.write(filas, 14, 'FIRMA', titulo2)
        sheet.write(filas, 17, 'FECHA : ', titulo2)
    #     workbook.close()
    #     output.seek(0)
    #     response.stream.write(output.read())
    #     output.close()

    def generar_planilla_csv(self):
        mes = str(self.payslip.date_end.month)
        if len(mes)<2:
            mes = '0' + str(int(mes))
        filename = 'PLA_' + str(self.compania.vat) + "_"+str(self.payslip.date_end.year)+ "_"+str(mes) + ".csv"
        aumentar = ""
        saltopagina = "\r\n"
        basico = incremento = horas_extra = bono_antiguedad = monto_pagado = bono_produccion = 0.00
        bono_dominical = otros_bonos = total_ganado = sip_patronal = sip_nacional = rc_iva = 0.00
        anticipo = total_descuento = liquido_pagable = odescuentos = 0.00
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip.id)])
        numero =0
        for pay in payslips:
            for slips in pay.line_ids:
                if slips.code == 'BASIC':
                    basico = slips.amount
                if slips.code == 'INCRE':
                    incremento = slips.amount
                if slips.code == 'BANTI':
                    bono_antiguedad = slips.amount
                if slips.code == 'BONOP':
                    bono_produccion = slips.amount
                if slips.code == 'BONOD':
                    bono_dominical = slips.amount
                if slips.code == 'OBONO':
                    otros_bonos = slips.amount
                if slips.code == 'GROSS':
                    total_ganado = slips.amount
                if slips.code == 'AFPAL':
                    sip_patronal = slips.amount
                if slips.code == 'AFPASN':
                    sip_nacional = slips.amount
                if slips.code == 'RCIVA':
                    rc_iva = slips.amount
                # if slips.code == 'ANTIC':
                #     anticipo = slips.amount
                if slips.code == 'ODESC':
                    odescuentos = slips.amount
                if slips.code == 'TDESC':
                    total_descuento = slips.amount
                if slips.code == 'NETO':
                    liquido_pagable = slips.amount

            numero += 1
            genero = ''
            if pay.employee_id.gender == 'male':
                genero = 'M'
            if pay.employee_id.gender == 'female':
                genero = 'F'
            if pay.employee_id.gender == 'other':
                genero = 'O'
            documento = ''
            if pay.employee_id.identification_id:
                documento = str(pay.employee_id.identification_id).split(' ')
            aumentar = aumentar + "|" + str(numero)
            aumentar = aumentar + "|" + str(documento[0])
            aumentar = aumentar + "|" + str(pay.employee_id.name)
            aumentar = aumentar + "|" + str(pay.employee_id.country_id.name)
            aumentar = aumentar + "|" + str(genero)
            aumentar = aumentar + "|" + str(pay.employee_id.job_title)
            aumentar = aumentar + "|" + str((datetime.strptime(str(pay.employee_id.contract_id.date_start), '%Y-%m-%d')).strftime('%d/%m/%Y'))
            aumentar = aumentar + "|" + str(pay.dias_trabajados)
            aumentar = aumentar + "|" + str(round(pay.employee_id.contract_id.wage))
            aumentar = aumentar + "|" + str(round(incremento))
            aumentar = aumentar + "|" + str('8')
            aumentar = aumentar + "|" + str(round(bono_antiguedad))
            aumentar = aumentar + "|" + str(horas_extra)
            aumentar = aumentar + "|" + str(round(monto_pagado))
            aumentar = aumentar + "|" + str(round(bono_produccion))
            aumentar = aumentar + "|" + str(round(bono_dominical))
            aumentar = aumentar + "|" + str(round(otros_bonos))
            aumentar = aumentar + "|" + str(round(total_ganado))
            aumentar = aumentar + "|" + str(round(sip_patronal))
            aumentar = aumentar + "|" + str(round(sip_nacional))
            aumentar = aumentar + "|" + str(round(rc_iva))
            aumentar = aumentar + "|" + str(round(odescuentos))
            aumentar = aumentar + "|" + str(round(total_descuento))
            aumentar = aumentar + "|" + str(round(liquido_pagable))
            aumentar = aumentar + saltopagina

            txt_planilla_csv = aumentar
        export_id = self.env['txt.extended']
        id_file = export_id.create({'txt_file': base64.b64encode(txt_planilla_csv.encode() or ' '), 'file_name': filename})

        return {
            'view_mode': 'form',
            'res_id': id_file.id,
            'res_model': 'txt.extended',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class HrPlanillaRetroactivo(models.Model):
    _inherit = 'hr.retroactivo.empleados'

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def action_generar_planilla(self):
        _logger.info(self)
        payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip_retro.id)])
        numero = 0
        self.state='activo'
        self.env.cr.execute("DELETE FROM hr_planilla_retroactivo WHERE planilla_id="+str(self.id))
        for pay in payslips:
            basicantretro = basicincreretro = bantiant = bantiactmi= eneroretro = beneroretro = febreroretro = bfebreroretro = 0.0
            marzoretro = bmarzoretro = abrilretro = babrilretro = mayoretro = bmayoretro = totalretro = afpalretro = 0.0
            rcivaretroa = descuentretro = tdescuentoretro = netoretro = 0.0
            for slips in pay.line_ids:
                if slips.code == 'BASICANTRETRO':
                    basicantretro = slips.amount
                if slips.code == 'BASICINCRETRO':
                    basicincreretro = slips.amount
                if slips.code == 'BANTIANT':
                    bantiant = slips.amount
                if slips.code == 'BANTIACTMI':
                    bantiactmi = slips.amount
                if slips.code == 'ENERORETRO':
                    eneroretro = slips.amount
                if slips.code == 'BENERORETRO':
                    beneroretro = slips.amount
                if slips.code == 'FEBRERORETRO':
                    febreroretro = slips.amount
                if slips.code == 'BFEBRERORETRO':
                    bfebreroretro = slips.amount
                if slips.code == 'MARZORETRO':
                    marzoretro = slips.amount
                if slips.code == 'BMARZORETRO':
                    bmarzoretro = slips.amount
                if slips.code == 'ABRILRETRO':
                    abrilretro = slips.amount
                if slips.code == 'BABRILRETRO':
                    babrilretro = slips.amount
                if slips.code == 'MAYORETRO':
                    mayoretro = slips.amount
                if slips.code == 'BMAYORETRO':
                    bmayoretro = slips.amount
                if slips.code == 'TOTALRETRO':
                    totalretro = slips.amount
                if slips.code == 'AFPALRETRO':
                    afpalretro = slips.amount
                if slips.code == 'RCIVARETROA':
                    rcivaretroa = slips.amount
                if slips.code == 'DESCUENTRETRO':
                    descuentretro = slips.amount
                if slips.code == 'TDESCUENTRETRO':
                    tdescuentoretro = slips.amount
                if slips.code == 'NETORETRO':
                    netoretro = slips.amount

            numero += 1
            genero = ''
            if pay.employee_id.gender == 'male':
                genero = 'M'
            if pay.employee_id.gender == 'female':
                genero = 'F'
            if pay.employee_id.gender == 'other':
                genero = 'O'
            self.env['hr.planilla.retroactivo'].create({
                'planilla_id':self.id,
                'empleado':pay.employee_id.id,
                'numero':numero,
                'genero':genero,
                'cargo':pay.employee_id.job_title,
                'fecha_ingreso':(datetime.strptime(str(pay.employee_id.contract_id.date_start), '%Y-%m-%d')).strftime('%d/%m/%Y'),
                'haber_basico_ant':round(basicantretro,2),
                'haber_basico_inc':round(basicincreretro,2),
                'bono_antiguedad_ant':round(bantiant,2),
                'bono_antiguedad_act':round(bantiactmi,2),
                'enero_retro':round(eneroretro,2),
                'bono_enero_retro':round(beneroretro,2),
                'febrero_retro':round(febreroretro,2),
                'bono_febrero_retro':round(bfebreroretro,2),
                'marzo_retro':round(marzoretro,2),
                'bono_marzo_retro':round(bmarzoretro,2),
                'abril_retro':round(abrilretro,2),
                'bono_abril_retro':round(babrilretro,2),
                'mayo_retro':round(mayoretro,2),
                'bono_mayo_retro':round(bmayoretro,2),
                'total_retroactivo':round(totalretro,2),
                'afp_retro':round(afpalretro,2),
                'rciva':round(rcivaretroa,2),
                'otros_descuentos':round(descuentretro,2),
                'total_descuentos':round(tdescuentoretro,2),
                'liquido_pagable':round(netoretro,2),
                })

    def _prepare_report_data(self):
        data = {
            'compania': self.compania.id,
            'run': self.payslip_retro.id,
        }
        return data

    def generar_planilla(self):
        self.ensure_one()
        data = self._prepare_report_data()
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)
        workbook.close()
        fout=encodebytes(file_io.getvalue())
        
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Planilla Retroactivos'
        filename = '%s_%s'%(report_name,datetime_string)
        self.write({'fileout':fout, 'fileout_filename':filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=fileout&download=true&filename='+filename,
        }

    def generar_planilla_csv(self):
        _logger.info(self)
        # mes = str(self.payslip.date_end.month)
        # if len(mes)<2:
        #     mes = '0' + str(int(mes))
        # filename = 'PLA_' + str(self.compania.vat) + "_"+str(self.payslip.date_end.year)+ "_"+str(mes) + ".csv"
        # aumentar = ""
        # saltopagina = "\r\n"
        # basico = incremento = horas_extra = bono_antiguedad = monto_pagado = bono_produccion = 0.00
        # bono_dominical = otros_bonos = total_ganado = sip_patronal = sip_nacional = rc_iva = 0.00
        # anticipo = total_descuento = liquido_pagable = odescuentos = 0.00
        # payslips = self.env['hr.payslip'].search([('payslip_run_id','=',self.payslip.id)])
        # numero =0
        # for pay in self.detalle_planilla:
        #     numero += 1
        #     genero = ''
        #     aumentar = aumentar + "|" + str(numero)
        #     aumentar = aumentar + "|" + str(pay.carnet or "")
        #     aumentar = aumentar + "|" + str(pay.employee_id.name)
        #     aumentar = aumentar + "|" + str(pay.cargo)
        #     aumentar = aumentar + "|" + str(pay.haber_basico_ant)
        #     aumentar = aumentar + "|" + str(pay.haber_basico_inc)
        #     aumentar = aumentar + "|" + str(pay.bono_antiguedad_ant)
        #     aumentar = aumentar + "|" + str(pay.bono_antiguedad_act)
        #     aumentar = aumentar + "|" + str(pay.enero_retro)
        #     aumentar = aumentar + "|" + str(pay.bono_enero_retro)
        #     aumentar = aumentar + "|" + str(pay.febrero_retro)
        #     aumentar = aumentar + "|" + str(pay.bono_febrero_retro)
        #     aumentar = aumentar + "|" + str(pay.marzo_retro)
        #     aumentar = aumentar + "|" + str(pay.bono_marzo_retro)
        #     aumentar = aumentar + "|" + str(pay.abril_retro)
        #     aumentar = aumentar + "|" + str(pay.bono_abril_retro)
        #     aumentar = aumentar + "|" + str(pay.mayo_retro)
        #     aumentar = aumentar + "|" + str(pay.bono_mayo_retro)
        #     aumentar = aumentar + "|" + str(pay.total_retroactivo)
        #     aumentar = aumentar + "|" + str(pay.afp_retro)
        #     aumentar = aumentar + "|" + str(pay.rciva)
        #     aumentar = aumentar + "|" + str(pay.otros_descuentos)
        #     aumentar = aumentar + "|" + str(pay.total_descuentos)
        #     aumentar = aumentar + "|" + str(pay.liquido_pagable)

        #     aumentar = aumentar + saltopagina

        #     txt_planilla_csv = aumentar
        # export_id = self.env['txt.extended']
        # id_file = export_id.create({'txt_file': base64.b64encode(txt_planilla_csv.encode() or ' '), 'file_name': filename})

        # return {
        #     'view_mode': 'form',
        #     'res_id': id_file.id,
        #     'res_model': 'txt.extended',
        #     'view_type': 'form',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        # }



    def generate_xlsx_report(self, workbook, data=None, objs=None):


        sheet = workbook.add_worksheet('Reporte de Planilla Retroactivos')
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
        sheet.set_column('Y:Y', 20) 

        #Titulos
        compania = self.env['res.company'].search([('id','=',data['compania'])])
        sheet.merge_range('A1:C1', 'NOMBRE O RAZON SOCIAL:', titulo2)
        sheet.merge_range('D1:F1', compania.name, titulo4)
        sheet.merge_range('A2:C2', 'DIRECCION:', titulo2)
        sheet.merge_range('D2:F2', compania.street, titulo4)
        sheet.merge_range('A3:C3', 'N° NIT:', titulo2)
        sheet.merge_range('D3:F3', compania.vat, titulo4)          
        sheet.merge_range('A4:C4', 'N° EMPLEADOR (CAJA DE SALUD)  CPS:   ', titulo2)
        sheet.merge_range('D4:F4', compania.nro_salud, titulo4)
        sheet.merge_range('A5:C5', 'N° EMPLEADOR MINISTERIO DE TRABAJO:', titulo2)
        sheet.merge_range('D5:F5', compania.nro_ministerio, titulo4)
        sheet.merge_range('A6:C6', 'REPRESENTANTE LEGAL:', titulo2)
        sheet.merge_range('D6:F6', compania.responsable_legal, titulo4)
        sheet.merge_range('A7:C7', 'N° C.I. REPRESENTANTE LEGAL', titulo2)
        sheet.merge_range('D7:F7', compania.ci_responsable_legal, titulo4)
        sheet.merge_range('A8:C8', 'DIRECCION:', titulo2)
        sheet.merge_range('D8:F8', compania.street2, titulo4)
        sheet.merge_range('A9:C9', 'TELEFONO:', titulo2)
        sheet.merge_range('D9:F9', compania.phone, titulo4)
        sheet.merge_range('A10:C10', 'CORREO:', titulo2)
        sheet.merge_range('D10:F10', compania.email, titulo4)
        # cadena = "CORRESPONDIENTE AL MES DE" 
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
        sheet.merge_range('A12:Y12', 'PLANILLA DE RETROACTIVO', titulo3)
        sheet.merge_range('A13:Y13', 'INCREMENTO SALARIAL '+str(payslips_run.date_end.year), titulo3)
        # sheet.merge_range('A14:Y14', 'PERSONAL PERMANENTE', titulo3)
        sheet.merge_range('A15:Y15', '( Expresado en Bolivianos )', titulo3)
        #Cabecera
        sheet.merge_range('A17:A18', 'Nº', cabecera1)
        sheet.merge_range('B17:B18', 'CARNET DE IDENTIDAD', cabecera1)
        sheet.merge_range('C17:C18', 'APELLIDOS Y NOMBRES', cabecera1)
        sheet.merge_range('D17:D18', 'SEXO\n(V/M)', cabecera1)
        sheet.merge_range('E17:E18', 'OCUPACION QUE DESEMPEÑA', cabecera1)
        sheet.merge_range('F17:F18', 'FECHA \n INGRESO', cabecera1)
        sheet.merge_range('G17:G18', 'HABER BASICO', cabecera1)
        sheet.merge_range('H17:H18', 'HABER BASICO CON \n INCREMENTO', cabecera1)
        sheet.merge_range('I17:I18', 'BONO DE ANTIGUEDAD', cabecera1)
        sheet.merge_range('J17:J18', 'BONO ANTIGUEDAD INCREMENTO', cabecera1)
        sheet.merge_range('K17:T17', 'MONTOS', cabecera1)
        sheet.write(17,10, 'ENERO.', cabecera1)
        sheet.write(17,11, 'BONO ANTIG \n ENERO', cabecera1)
        sheet.write(17,12, 'FEBRERO.', cabecera1)
        sheet.write(17,13, 'BONO ANTIG \n FEBRERO', cabecera1)
        sheet.write(17,14, 'MARZO.', cabecera1)
        sheet.write(17,15, 'BONO ANTIG \n MARZO', cabecera1)
        sheet.write(17,16, 'ABRIL.', cabecera1)
        sheet.write(17,17, 'BONO ANTIG \n ABRIL', cabecera1)
        sheet.write(17,18, 'MAYO.', cabecera1)
        sheet.write(17,19, 'BONO ANTIG \n MAYO', cabecera1)
        sheet.merge_range('U17:U18', 'TOTALES RETROACTIVO', cabecera1)
        sheet.merge_range('V17:X17', 'DESCUENTOS', cabecera1)
        sheet.write(17,21, 'AFP.', cabecera1)
        sheet.write(17,22, 'RC-IVA', cabecera1)
        sheet.write(17,23, 'OTROS DESCUENTOS.', cabecera1)
        sheet.merge_range('Y17:Y18', 'TOTAL DESCUENTOS', cabecera1)
        sheet.merge_range('Z17:Z18', 'LIQUIDO PAGABLE', cabecera1)
        numero = 1
        filas = 18
        thaber_basico_ant = 0
        thaber_basico_inc = 0
        tbono_antiguedad_ant = 0
        tbono_antiguedad_act = 0
        tenero_retro = 0
        tbono_enero_retro = 0
        tfebrero_retro = 0
        tbono_febrero_retro = 0
        tmarzo_retro = 0
        tbono_marzo_retro = 0
        tabril_retro = 0
        tbono_abril_retro = 0
        tmayo_retro = 0
        tbono_mayo_retro = 0
        ttotal_retroactivo = 0
        tafp_retro = 0
        trciva = 0
        totros_descuentos = 0
        ttotal_descuentos = 0
        tliquido_pagable = 0
        for pay in self.detalle_planilla:
            sheet.write(filas, 0, numero, valor_formato1)
            sheet.write(filas, 1, str(pay.carnet or ""), valor_formato2) 
            sheet.write(filas, 2, pay.empleado.name, valor_formato1) 
            sheet.write(filas, 3, pay.genero, valor_formato1) 
            sheet.write(filas, 4, pay.cargo, valor_formato1) 
            sheet.write(filas, 5, pay.fecha_ingreso, valor_formato1) 
            sheet.write(filas, 6, pay.haber_basico_ant, valor_formato1) 
            thaber_basico_ant+=float(pay.haber_basico_ant)
            sheet.write(filas, 7, pay.haber_basico_inc, valor_formato1) 
            thaber_basico_inc+=float(pay.haber_basico_inc)
            sheet.write(filas, 8, pay.bono_antiguedad_ant, valor_formato1) 
            tbono_antiguedad_ant+=float(pay.bono_antiguedad_ant)
            sheet.write(filas, 9, pay.bono_antiguedad_act, valor_formato1) 
            tbono_antiguedad_act+=float(pay.bono_antiguedad_act)
            sheet.write(filas, 10, pay.enero_retro, valor_formato1) 
            tenero_retro+=float(pay.enero_retro)
            sheet.write(filas, 11, pay.bono_enero_retro, valor_formato1) 
            tbono_enero_retro+=float(pay.bono_enero_retro)
            sheet.write(filas, 12, pay.febrero_retro, valor_formato1) 
            tfebrero_retro+=float(pay.febrero_retro)
            sheet.write(filas, 13, pay.bono_febrero_retro, valor_formato1) 
            tbono_febrero_retro+=float(pay.bono_febrero_retro)
            sheet.write(filas, 14, pay.marzo_retro, valor_formato1) 
            tmarzo_retro+=float(pay.marzo_retro)
            sheet.write(filas, 15, pay.bono_marzo_retro, valor_formato1) 
            tbono_marzo_retro+=float(pay.bono_marzo_retro)
            sheet.write(filas, 16, pay.abril_retro, valor_formato1) 
            tabril_retro+=float(pay.abril_retro)
            sheet.write(filas, 17, pay.bono_abril_retro, valor_formato1) 
            tbono_abril_retro+=float(pay.bono_abril_retro)
            sheet.write(filas, 18, pay.mayo_retro, valor_formato1) 
            tmayo_retro+=float(pay.mayo_retro)
            sheet.write(filas, 19, pay.bono_mayo_retro, valor_formato1) 
            tbono_mayo_retro+=float(pay.bono_mayo_retro)
            sheet.write(filas, 20, pay.total_retroactivo, valor_formato1) 
            ttotal_retroactivo+=float(pay.total_retroactivo)
            sheet.write(filas, 21, pay.afp_retro, valor_formato1) 
            tafp_retro+=float(pay.afp_retro)
            sheet.write(filas, 22, pay.rciva, valor_formato1) 
            trciva+=float(pay.rciva)
            sheet.write(filas, 23, pay.otros_descuentos, valor_formato1) 
            totros_descuentos+=float(pay.otros_descuentos)
            sheet.write(filas, 24, pay.total_descuentos, valor_formato1) 
            ttotal_descuentos+=float(pay.total_descuentos)
            sheet.write(filas, 25, pay.liquido_pagable, valor_formato1) 
            tliquido_pagable+=float(pay.liquido_pagable)


            filas += 1
            numero += 1
        sheet.write(filas, 5, 'TOTALES', cabecera1)
        sheet.write(filas, 6, thaber_basico_ant, total_formato3)
        sheet.write(filas, 7, thaber_basico_inc, total_formato3)
        sheet.write(filas, 8, tbono_antiguedad_ant, total_formato3)
        sheet.write(filas, 9, tbono_antiguedad_act, total_formato3)
        sheet.write(filas, 10, tenero_retro, total_formato3)
        sheet.write(filas, 11, tbono_enero_retro, total_formato3)
        sheet.write(filas, 12, tfebrero_retro, total_formato3)
        sheet.write(filas, 13, tbono_febrero_retro, total_formato3)
        sheet.write(filas, 14, tmarzo_retro, total_formato3)
        sheet.write(filas, 15, tbono_marzo_retro, total_formato3)
        sheet.write(filas, 16, tabril_retro, total_formato3)
        sheet.write(filas, 17, tbono_abril_retro, total_formato3)
        sheet.write(filas, 18, tmayo_retro, total_formato3)
        sheet.write(filas, 19, tbono_mayo_retro, total_formato3)
        sheet.write(filas, 20, ttotal_retroactivo, total_formato3)
        sheet.write(filas, 21, tafp_retro, total_formato3)
        sheet.write(filas, 22, trciva, total_formato3)
        sheet.write(filas, 23, totros_descuentos, total_formato3)
        sheet.write(filas, 24, ttotal_descuentos, total_formato3)
        sheet.write(filas, 25, tliquido_pagable, total_formato3)
        filas += 4
        sheet.write(filas, 7, compania.responsable_legal, titulo2)
        sheet.write(filas, 10, compania.ci_responsable_legal, titulo2)
        sheet.write(filas, 14, '__________________________', titulo2)
        filas += 1
        sheet.write(filas, 7, 'NOMBRE DEL EMPLEADOR O REPRESENTANTE LEGAL', titulo2)
        sheet.write(filas, 10, 'N° DE DOCUMENTO DE IDENTIDAD', titulo2)
        sheet.write(filas, 14, 'FIRMA', titulo2)
        sheet.write(filas, 17, 'FECHA : ', titulo2)
