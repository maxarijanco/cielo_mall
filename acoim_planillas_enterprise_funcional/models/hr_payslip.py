# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta, date
from odoo.exceptions import AccessError, UserError, ValidationError
import json
import io
import calendar

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

    def mes_anio(self,fecha):
        fecha_final = str(fecha)
        cadena_separada = fecha_final.split('-')
        dia = cadena_separada[2]
        mes = cadena_separada[1]
        anio = cadena_separada[0]
        cadena_final = ''
        if mes == '01': mes= '01'
        if mes == '02': mes= '02'
        if mes == '03': mes= '03'
        if mes == '04': mes= '04'
        if mes == '05': mes= '05'
        if mes == '06': mes= '06'
        if mes == '07': mes= '07'
        if mes == '08': mes= '08'
        if mes == '09': mes= '09'
        if mes == '10': mes= '10'
        if mes == '11': mes= '11'
        if mes == '12': mes= '12'

        return mes +"/"+str(anio)

    def detalle_mes(self,fecha):
        fecha_final = str(fecha)
        cadena_separada = fecha_final.split('-')
        dia = cadena_separada[2]
        mes = cadena_separada[1]
        anio = cadena_separada[0]
        cadena_final = ''
        if mes == '01': mes= 'Enero'
        if mes == '02': mes= 'Febrero'
        if mes == '03': mes= 'Marzo'
        if mes == '04': mes= 'Abril'
        if mes == '05': mes= 'Mayo'
        if mes == '06': mes= 'Junio'
        if mes == '07': mes= 'Julio'
        if mes == '08': mes= 'Agosto'
        if mes == '09': mes= 'Septiembre'
        if mes == '10': mes= 'Octubre'
        if mes == '11': mes= 'Noviembre'
        if mes == '12': mes= 'Diciembre'

        return mes +" de "+str(anio)


    def detalle_dia_mes(self,fecha):
        fecha_final = str(fecha)
        cadena_separada = fecha_final.split('-')
        dia = cadena_separada[2]
        mes = cadena_separada[1]
        anio = cadena_separada[0]
        cadena_final = ''
        if mes == '01': mes= 'Enero'
        if mes == '02': mes= 'Febrero'
        if mes == '03': mes= 'Marzo'
        if mes == '04': mes= 'Abril'
        if mes == '05': mes= 'Mayo'
        if mes == '06': mes= 'Junio'
        if mes == '07': mes= 'Julio'
        if mes == '08': mes= 'Agosto'
        if mes == '09': mes= 'Septiembre'
        if mes == '10': mes= 'Octubre'
        if mes == '11': mes= 'Noviembre'
        if mes == '12': mes= 'Diciembre'

        return dia + "de " + str(mes) +" de "+str(anio)

    def numero_texto(self, monto_total, moneda):
        tmp = str(monto_total).split('.')
        entero = monto_total
        decimales = '0'
        currency = self.env['res.currency'].search([('symbol','=',str(moneda))])
        if len(tmp) > 1:
            entero = int(tmp[0])
            decimales = tmp[1]
        texto_final = convertir_texto.integer_to_word(entero)
        texto_final += convertir_texto.decimal_number_to_text(decimales)
        if currency:
            texto_final += currency.currency_unit_label 
        elif moneda == "$":
            texto_final += "Dolares"
        elif moneda == "Bs.":
            texto_final += 'Bolivianos'
        else:
            texto_final += str(moneda)

        return (texto_final[:1].upper() + texto_final[1:])


    def current_moneda(self,valor):
        moneda = self.env['res.currency'].search([('name','=','USD')])
        _logger.info(moneda)
        for order in self:
            valores = moneda._get_conversion_rate(order.currency_id, moneda, order.company_id, order.date_to)
            if valores:
                return round(float(1/float(valores)),2)
            else:
                return '1.0'


    def action_print_payslip(self):
        return self.env.ref('acoim_planillas_enterprise_funcional.planilla_carta').report_action(self)

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_retroactivo(self):
        for line in self:
            porcentaje = 0
            aniotrabajado = (line.date_from).year
            mestrabajado = str((line.date_from).month)
            if int(mestrabajado)<10:
                mestrabajado = '0'+ str(mestrabajado)
            registro_porcentaje = self.env['hr.retroactivos'].search([('anio','=',aniotrabajado),('state','=','activo'),('compania','=',line.company_id.id)])
            porcentaje = 0
            enero = febrero = marzo = abril = mayo = False
            if registro_porcentaje:
                detalle = self.env['hr.retroactivos.detalle'].search([('empleado','=',line.employee_id.id),('detalle_id','=',registro_porcentaje.id)])
                if detalle:
                    porcentaje = detalle.porcentaje
                for meses in registro_porcentaje.meses:
                    mes = meses.codigo
                    if len(str(mes))<2:
                        mes = '0' + str(int(mes))
                    dias_mes = calendar.monthrange(aniotrabajado,int(mes))
                    inicio_mes = str(aniotrabajado) + '-' + str(mes) + '-' + str('01')
                    fin_mes = str(aniotrabajado) + '-' + str(mes) + '-' + str(dias_mes[1])
                    _logger.info(inicio_mes)
                    _logger.info(fin_mes)
                    _logger.info(mes)
                    registro = self.env['hr.payslip'].search([('employee_id','=',line.employee_id.id),('date_from','=',str(inicio_mes)),('date_to','=',str(fin_mes)),('retroactivo','=',False)])
                    
                    if int(meses.codigo) == 1:
                        # _logger.info(registro.retroactivo)
                        _logger.info("registro")
                        if registro:
                            enero = registro
                    if int(meses.codigo) == 2:
                        if registro:
                            febrero = registro
                    if int(meses.codigo) == 3:
                        if registro:
                            marzo = registro
                    if int(meses.codigo) == 4:
                        if registro:
                            abril = registro
                    if int(meses.codigo) == 5:
                        if registro:
                            mayo = registro

            line.porcentaje = porcentaje
            line.retroactivo = line.payslip_run_id.retroactivo
            line.retro_enero = enero
            line.retro_febrero = febrero
            line.retro_marzo = marzo
            line.retro_abril = abril
            line.retro_mayo = mayo
    
    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_values(self):
        for line in self:
            def salario_basico(fecha,compania):
                cadena = str(fecha).split('-')
                self.env.cr.execute("SELECT id,fecha,monto FROM hr_salario_basico WHERE date_part('year',fecha) = '"+str(cadena[0])+"'ORDER BY id ASC")
                valor = [i for i in self.env.cr.fetchall()]
                minimo = 0
                if valor:
                    for salariobasico in valor:
                        _logger.info(salariobasico[1].month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(salariobasico[2])
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)
                        _logger.info(fecha.month)                        
                        if (salariobasico[1].month <= fecha.month) and minimo==0:
                            minimo = str(salariobasico[2])
                        elif line.retroactivo == False:
                            if salariobasico[1].month <= fecha.month:
                                minimo = str(salariobasico[2])
                else:
                    raise UserError(_("El año correspondiente al registro, no cuenta con un salario basico. \n Por favor registre un salario minimo para el año correspondiente"))
                return minimo


            def salario_basico_act(fecha,compania):
                cadena = str(fecha).split('-')
                self.env.cr.execute("SELECT id,fecha,monto FROM hr_salario_basico WHERE date_part('year',fecha) = '"+str(cadena[0])+"'ORDER BY id DESC LIMIT 1")
                valor = [i for i in self.env.cr.fetchall()]
                minimo = 0
                contador = 0
                if valor:
                    for salario in valor:
                        minimo = str(salario[2])
                else:
                    raise UserError(_("El año correspondiente al registro, no cuenta con un salario basico. \n Por favor registre un salario minimo para el año correspondiente"))
                
                return minimo


            def descuento_personal(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(monto) FROM hr_descuentos where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha_descuento  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                descuento = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return descuento

            def descuento_anticipos(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(monto) FROM hr_anticipos where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                anticipos = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return anticipos

            def bono_personal(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(monto) FROM hr_bono where modo_bono='Porcentual' and employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha_bono  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"' GROUP BY modo_bono")
                resultado_porcentual = [i[0] for i in self.env.cr.fetchall()]
                self.env.cr.execute("SELECT SUM(monto) FROM hr_bono where modo_bono='Monetario' and employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha_bono  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"' GROUP BY modo_bono")
                resultado_monetario = [i[0] for i in self.env.cr.fetchall()]
                bono =  monto_porcentual = monto_monetario = 0
                if len(resultado_porcentual)>0:
                    monto_porcentual = float(monto) *  (resultado_porcentual[0] / 100.0) 
                if len(resultado_monetario)>0:
                    monto_monetario = resultado_monetario[0]
                return (monto_porcentual+monto_monetario)

            def incremento_salarial(fecha,compania):
                cadena = str(fecha).split('-')
                self.env.cr.execute("SELECT aumento_salario_basico FROM hr_incremento_salarial WHERE date_part('year',fecha_promulgacion) = '"+str(cadena[0])+"' ORDER BY id DESC LIMIT 1")
                valor = [i[0] for i in self.env.cr.fetchall()]
                minimo = 0
                if len(valor)>0:
                    return valor[0]

            def bono_antiguedad(anios,compania):
                self.env.cr.execute("SELECT monto FROM hr_bono_antiguedad WHERE anio_inicial<="+ str(anios) +" AND anio_final>"+ str(anios) +" LIMIT 1")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                resultado = 0
                if resultado_consulta:
                    resultado = resultado_consulta[0]
                return resultado

            def facturas_presentadas(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(monto) FROM hr_asignacion_facturas_presentadas where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                descuento = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return descuento

            def facturas_retenciones(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(monto) FROM hr_asignacion_facturas_retencion where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                retencion = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return retencion

            def saldo_favor_dependiente(empleado,fecha_inicial,fecha_final,compania):
                anio = (line.date_from).year
                mes = str((line.date_from).month)

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
            
            def horas_extras_realizadas(empleado,fecha_inicial,fecha_final,compania):
                self.env.cr.execute("SELECT SUM(valor) FROM hr_asignacion_horas_extra where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha_asignada  BETWEEN '" + str(fecha_inicial)+"' AND '"+str(fecha_final)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                horas = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return horas

            def saldo_favor_dependiente_retenciones(empleado,fecha_inicial,fecha_final,compania):
                anio = (line.date_from).year
                mes = str((line.date_from).month)

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
                    mes_anterior = mes
                dias_mes = calendar.monthrange(anio,int(mes_anterior))
                inicio_mes = str(anio) + '-' + str(mes_anterior) + '-' + str('01')
                fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
                self.env.cr.execute("SELECT SUM(monto) FROM hr_asignacion_saldo_favor_retencion where employee="+ str(empleado) +" and company_id="+ str(compania) +" and fecha  BETWEEN '" + str(inicio_mes)+"' AND '"+str(fin_mes)+"'")
                resultado_consulta = [i[0] for i in self.env.cr.fetchall()]
                saldo = 0
                if resultado_consulta[0] is not None:
                    return resultado_consulta[0]
                else:
                    return saldo

            descuento = bono = incremento = antiguedad = extra = salario_minimo = salario_minimo_act = facturas =  saldo_favor_dependiente_ant = retenciones = saldo_favor_retencion_ant = 0.00
            anticipo = ufv_ini = ufv_fin= 0.00
            anios_empl=0
            dias_trabajados=0
            jubilado_empleado = False
            fecha_actual=(datetime.now()-timedelta(hours=4)).strftime('%Y-%m-%d')
            
            if line.employee_id:
                moneda = self.env['res.currency'].search([('name','=','UFV'),('active','=',True)])
                jubilado_empleado = line.employee_id.jubilado
                if moneda:
                    anio = (line.date_from).year
                    mes = str((line.date_from).month)

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
                    cambio_ini = self.env['res.currency.rate'].search([('name','=',str(fin_mes)),('currency_id','=',moneda.id),('company_id','=',line.company_id.id)])
                    if cambio_ini:
                        ufv_ini = cambio_ini.rate
                    else:
                        raise UserError(_("El año o mes correspondiente no cuenta con una moneda de cambio para la fecha "+str(fin_mes)+". \n Por favor registre un cambio en UFV correspondiente a la fecha"))
       
                    cambio_fin = self.env['res.currency.rate'].search([('name','=',str(line.date_to)),('currency_id','=',moneda.id),('company_id','=',line.company_id.id)])
                    if cambio_fin:
                        ufv_fin = cambio_fin.rate
                    else:
                        raise UserError(_("El año o mes correspondiente no cuenta con una moneda de cambio para la fecha "+str(line.date_to)+". \n Por favor registre un cambio en UFV correspondiente a la fecha"))
       
                h1 = datetime.strptime(str(line.employee_id.contract_id.date_start), '%Y-%m-%d').year
                h2 = datetime.strptime(fecha_actual, '%Y-%m-%d').year
                
                self.env.cr.execute("select date_part('year', age('"+str(line.employee_id.contract_id.date_start)+"', '"+str(line.date_to)+"'))")
                anios_pos = [i[0] for i in self.env.cr.fetchall()]
                self.env.cr.execute("select date_part('year', age('"+str(line.employee_id.birthday)+"', '"+str(line.date_to)+"'))")
                empleado_anios = [i[0] for i in self.env.cr.fetchall()]
                dias = anios_pos[0]
                salario_minimo = salario_basico(line.date_to,line.company_id.id)
                salario_minimo_act = salario_basico_act(line.date_to,line.company_id.id)
                incremento = incremento_salarial(line.date_to,line.company_id.id)
                descuento = descuento_personal(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                anticipo = descuento_anticipos(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                bono = bono_personal(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                antiguedad = bono_antiguedad(abs(anios_pos[0]),line.company_id.id)
                anios_empl = abs(empleado_anios[0])
                facturas = facturas_presentadas(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                retenciones = facturas_retenciones(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                extra = horas_extras_realizadas(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                anio = (line.date_from).year
                mes = str((line.date_from).month)
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
                    mes_anterior = mes
                dias_mes = calendar.monthrange(anio,int(mes_anterior))
                inicio_mes = str(anio) + '-' + str(mes_anterior) + '-' + '01'
                fin_mes = str(anio) + '-' + str(mes_anterior) + '-' + str(dias_mes[1])
                registro = self.env['hr.payslip'].search([('employee_id','=',line.employee_id.id),('date_from','=',str(inicio_mes)),('date_to','=',str(fin_mes)),('retroactivo','=',False)])
                if registro:
                    planilla_iva = self.env['hr.planilla.iva'].search([('payslip','=',registro.payslip_run_id.id)])
                    if planilla_iva:
                        planilla_iva_detalle = self.env['hr.planilla.empleado.iva'].search([('planilla_id','=',planilla_iva.id),('empleado','=',line.employee_id.id)])
                        if planilla_iva_detalle:
                            saldo_favor_dependiente_ant = float(planilla_iva_detalle.saldo_siguiente_mes)
                            saldo_favor_retencion_ant = float(planilla_iva_detalle.saldo_retencion_siguiente_mes)
                else:
                    saldo_favor_dependiente_ant = saldo_favor_dependiente(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)
                    saldo_favor_retencion_ant = saldo_favor_dependiente_retenciones(line.employee_id.id,line.date_from,line.date_to,line.company_id.id)

            anio_trabajado = (line.date_from).year
            mes_trabajado = str((line.date_from).month)
            if int(mes_trabajado)<10:
                mes_trabajado = '0'+ str(mes_trabajado)
            registro = self.env['hr.dias.trabajados'].search([('anio','=',anio_trabajado),('mes','=',mes_trabajado),('state','=','activo'),('compania','=',line.company_id.id)])
            if registro:
                detalle = self.env['hr.dias.trabajados.detalle'].search([('empleado','=',line.employee_id.id),('detalle_id','=',registro.id)])
                if detalle:
                    dias_trabajados = detalle.dias_trabajados

            line.total_descuentos = descuento
            line.total_bonos = bono
            line.total_anticipos = anticipo
            line.incremento = incremento
            line.salario_minimo = salario_minimo
            line.salario_minimo_act = salario_minimo_act
            line.bono_antiguedad = antiguedad
            line.horas_extra = extra
            line.facturas_presentadas = facturas
            line.facturas_retenciones = retenciones
            line.saldo_favor_depend_ant = saldo_favor_dependiente_ant
            line.saldo_favor_reten_ant = saldo_favor_retencion_ant
            line.ufv_inicial = ufv_ini
            line.ufv_final = ufv_fin
            line.anios_empleado = anios_empl
            line.jubilado = jubilado_empleado
            line.dias_trabajados = dias_trabajados


