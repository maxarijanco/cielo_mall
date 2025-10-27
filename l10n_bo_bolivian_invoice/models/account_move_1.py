# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import pytz
from lxml import objectify
from odoo.addons.l10n_bo_bolivian_invoice.tools.utils import *
#from ..tools.utils import *
import gzip
import hashlib
import base64
#import io
#import tarfile
#from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
import xml.etree.ElementTree as ET

import random

from odoo.exceptions import ValidationError

import os
#import xmlschema
from lxml import etree


import logging
_logger = logging.getLogger(__name__)





class AccountMove1(models.Model):
    _inherit = ['account.move']

    def _post(self, soft=True):
        res =  super(AccountMove1, self)._post(soft)
        for record in res:
            if record.edi_bo_invoice and record.move_type in ['out_invoice','out_refund'] and not record.reversion:
                record.prepare_invoice()
                if not record.transaccion and record.pos_id.getEmisionCode() == 1:
                    raise UserError(f"OBSERVACIONES: {[error.description for error in record.messagesList_ids] if record.messagesList_ids else 'NINGUNO'} - ERRORES: {record.error if record.error else 'NINGUNO'}")
                record._action_post()
                
        return res
    
    
    def getUrl(self):
        URL = self.env['l10n.bo.wsdl'].search([('service_type','=','qr'),('environment_type','=',self.company_id.getL10nBoCodeEnvironment())], limit=1)
        if URL:
            return URL.wsdl
        raise UserError('No se encontro el servicio wsdl QR')
    
    def _action_post(self):
        self.write(
            {
                'url' : self.getUrl() + f'?nit={self.company_id.getNit()}&cuf={self.cuf}&numero={self.getInvoiceNumber()}&t={self.pos_id.paper_format_type}',
            }
        )
        if self.pos_id.emision_id.getCode() == 1: 
            pass
            #self.write({'invoice_date_edi' : self.get_datetime(),})
        if self.is_card:
            self.write({'card' : self.getCard()})
        if self.email_send:
            self.l10n_bo_send_mailing()

    def generatePdf(self):
        pdf = self.env.ref('l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo').render_qweb_pdf(self.ids)[0]
        _name_file = f'{self.pos_id.getCode()}-{self.document_type_id.getCode()}-{self.getInvoiceNumber()}'
        
        attacht_id = self.env['ir.attachment'].search(
            [('res_model', '=', self._name), ('res_id', '=', self.id), ('name', '=', _name_file)], limit=1)
        if not attacht_id:
            attacht_id = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': _name_file,
                'datas': base64.b64encode(pdf),
                'mimetype': 'application/pdf',
            })
        else:
            attacht_id.write({'datas': base64.b64encode(pdf), 'mimetype': 'application/pdf',})
        return attacht_id
    

    
    def l10n_bo_send_mailing(self):
        report = self.env.ref(f'l10n_bo_bolivian_invoice.ir_actions_report_invoice_bo_{self.pos_id.paper_format_type}')
        email_template_obj = self.env.ref('l10n_bo_bolivian_invoice.l10n_bo_send_gmail_template')
        if report:
            email_template_obj.update(
                {
                    'report_template_ids' : [(4,report.id)]
                }
            )
        _with_context_attach = [(4,self.generate_xml().id)]
        email_values = {'attachment_ids': _with_context_attach}
        email_template_obj.send_mail(self.id, force_send=True, email_values=email_values)
        self.sudo().env['mail.mail'].process_email_queue()
        email_template_obj.write({'report_template_ids' : False})
            

    """
        Validar que el documento exista en el punto de venta
    """

    def generate_xml(self):
        if not self.edi_str:
            self.str_edi_format()
        edi_str = str(self.edi_str)
        #raise UserError(edi_str)
        #edi_str = edi_str.encode('utf-8')
        objectify.fromstring(edi_str)
        
        #raise UserError('Hola 4')
        if self.company_id.getL10nBoCodeModality() == '1':
            if  "http://www.w3.org/2000/09/xmldsig#" not in self.signed_edi_str.decode('utf-8') or "Signature" not in self.signed_edi_str.decode('utf-8'):
                self.sign_edi_str()
            edi_tree_signed = self.signed_edi_str
            #raise UserError(f"{edi_tree_signed}")
        else:
            edi_tree_signed = edi_str.encode('utf-8')
        _name_file = f'{self.company_id.getNit()}-{self.name}'
        attacht_id = self.env['ir.attachment'].search(
            [('res_model', '=', self._name), ('res_id', '=', self.id), ('name', '=', _name_file)], limit=1)
        if not attacht_id:
            attacht_id = self.env['ir.attachment'].create({
                'res_model': self._name,
                'res_id': self.id,
                'type': 'binary',
                'name': _name_file,
                'datas': base64.b64encode(edi_tree_signed),
                'mimetype': 'application/xml',
            })
        else:
            attacht_id.write({'datas': base64.b64encode(edi_tree_signed), 'mimetype': 'application/xml',})
        return attacht_id
    

    def checkConection(self):
        if not self.pos_id.verificarComunicacion() and self.pos_id.getEmisionCode() == 1:
            raise UserError('Sin coneccion con la base de datos del SIN')
            self.pos_id.action_offline()
            _logger.info(self.pos_id.getEmisionCode())

    

            
    def prepare_invoice(self, massive = None):
        for record in self:
            #raise UserError(record.document_type_id.name.getCode() in [1,2] and not massive)
            pos_code_state = record.pos_id.getEmisionCode()
            invoice_post_outline = False
            #record.checkConection()
            if pos_code_state != record.pos_id.getEmisionCode():
                invoice_post_outline = True
            if record.invoice_type_code == 3 and record.pos_id.emision_code == 2:
                raise UserError('SERVICIO NO DISPONIBLE')
            
            record.check_partner_id()
            record.check_payment_type()
            record.write({'legend_id' : record.get_legend_default()})
            record.item_number_assigned()
            # 1 : ESTABLECER LA FECHA DE EMISION

            if (record.pos_id and record.pos_id.emision_code == 1) or invoice_post_outline:
                record.write({'invoice_date_edi' : fields.datetime.now()})
            else:
                if record.pos_id and record.pos_id.emision_code == 2:
                    record.get_enconomic_activities_in_invoice_line(mark_invoice=True) 
                    record.write({'legend_id' : record.get_legend_default(_global=False)})
            
                    if record.pos_id.event_id:
                        if record.pos_id.event_id.date_init:
                            if record.pos_id.event_id.date_init > record.invoice_date_edi:
                                raise UserError('La fecha de la factura no puede ser menor a la fecha de inicio del evento.')
                        else:
                            raise UserError("Su evento significativo no tiene una fecha de inicio")
                        
                        event_code = record.pos_id.event_id.getEventCode()
                        if not event_code:
                            raise UserError('Evento significativo no tiene un codigo de tipo de evento')

                    else:
                        raise UserError(f"No se encontro un evento significativo para el {record.pos_id.name}")
                else:
                    raise UserError("Las emisiones validas son EN LINEA(1) y FUERA DE LINEA(2)")

            
            #record.write({'invoice_date' : record.get_datetime_bo()})
            #_logger.info(f"Fecha odoo: {record.invoice_date}")
            
            if record.getInvoiceNumber() == 0:
                if not record.document_type_id:
                    record._set_default_document_type()
                invoice_number = 0
                if record.pos_id.getEmisionCode() == 1 or (record.pos_id.getEmisionCode() == 2 and record.pos_id.event_id.getEventCode() not in [5,6,7]):
                    invoice_number = record.pos_id.getSequence(record.document_type_id)
                elif record.pos_id.getEmisionCode() == 2 and record.pos_id.event_id.getEventCode() in [5,6,7]:
                    record.write({'manual_invoice' : True})
                    invoice_number = record.get_cafc_id(get_sequence=True)
                if invoice_number>0:
                    record.write({'invoice_number': invoice_number})
                else:
                    raise UserError('No se genero un correlativo para la factura')

            record.write({'meridies' : 'am' if int(self.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz')).strftime('%H')) < 12 else 'pm'})

            
            # 2 : GENERAR CUF PARA LA FACTURA
            
            _cuf = record.generateCuf()
            record.write({'cuf' : _cuf})
            record.write({'edi_str' : record.str_edi_format()})
            _logger.info(f'EDI STR: {record.edi_str}')
            edi_str = record.edi_str
            if record.edi_str in [None, False, '']:
                raise UserError(f'No tiene disponible una implementacion para el documento: {record.document_type_id.name.name}')
            
            if record.company_id.getL10nBoCodeModality() == '1':
                _logger.info('FIRMA')
                record.sign_edi_str()
                edi_str = record.signed_edi_str
            
            record.validate_xml(edi_str, record.get_xsd_path())
                
            if record.pos_id.getEmisionCode() == 1:
                record.generate_zip()
                record.write({'hash'              : hashlib.sha256(record.zip_edi_str).hexdigest()})
                record.send_invoice()

            



    def check_payment_type(self):
        for record in self:
            amount_giftcard = self.getAmountGiftCard()
            amount_discount = self.getAmountDiscount()
            self.prorate_prepare()
            if self.document_type_id.name.getCode() in [4,47] and amount_discount > 0:
                raise UserError('Los descuentos globales estan inhabilitados para este sector.')
            
            if record.is_gift_card and record.document_type_id.name.getCode() in [2]:
                raise UserError(f'El pago con gifcard no es valido para el documento: {self.document_type_id.name.name}')
            
            if record.is_gift_card and amount_giftcard == 0:
                raise UserError("El monto giftcard debe ser mayor a cero '0.00'")
            #elif record.is_gift_card and amount_giftcard >= self.getAmountTotal():
            #    raise UserError("El monto giftcard no debe ser mayor al monto total")
            
            
            # if amount_discount >= self.getAmountSubTotal() and self.invoice_line_ids.filtered(lambda l: l.product_id.global_discount):
            #     raise UserError("El monto descuento no debe ser mayor o igual al subtotal")
            
            if (record.is_card and not record.card) or (record.card and len(record.card) < 16):
                raise UserError("La tarjeta debe tener 16 caracteres")
            
    
    def prorate_prepare(self):
        if self.document_type_id.name.invoice_type_id.getCode() in [1]:
            amount_subtotal = self.getAmountSubTotal()
            amount_discount = self.getAmountDiscount()
            for line_id in self.invoice_line_ids:
                line_id.apportionment(amount_subtotal, amount_discount)
                

    def sign_edi_str(self):
        if  not self.company_id.getGrandParent().l10n_bo_edi_certificate_id:
            raise UserError('La compañia no tiene un certificado digital')
        success = False
        tries = 5
        while not success and tries>0:
            self.write({'signed_edi_str'    : self.company_id.getCertificate().sudo()._sign(objectify.fromstring(self.edi_str))})
            signed_str = str(self.signed_edi_str.decode('utf-8'))
            success = "http://www.w3.org/2000/09/xmldsig#" in signed_str or "Signature" in signed_str
            tries -= 1

        if tries<=0 or not success:
            raise UserError(f"Factura: {self.name}, Error al firmar documento")
    
    def zip_edi_document(self, param):
        return gzip.compress(param)

    def generate_zip(self):
        success = False
        tries = 5
        error = None
        while not success and tries>0:
            try:        
                params_src = self.generate_xml().datas
                params_src = base64.b64decode(params_src)
                self.write({'zip_edi_str': self.zip_edi_document(params_src)})
                success = True
                _logger.info('GZIP creado')
            except Exception as e:
                _logger.info(f'{e}')
                tries -=1
                error = e
                success = False
                _logger.info('Error al generar GZIP')
        if (tries<=0 or not success) and error:
            raise UserError(f'ERROR AL GENERAR ARCHIVO ZIP: {error}')
                
    def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))
        if MODALITY_TYPE:
            PARAMS.append(('modality_type','=', MODALITY_TYPE))
        
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS)
        
        if WSDL_SERVICE:
            #raise UserError(f'{PARAMS}')
            return getattr(self, f"{METHOD}")(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')

    def getAvailableDocument(self) -> list:
        return [
            1, # COMPRA VENTA
            24,# NOTA DE CREDITO DEBITO
            47 # NOTA DE CREDITO DEBITO DESCUENTOS
        ]
    

    def getReceptionMethod(self):
        return self.document_type_id.name.getReceptionMethod()
    
    def getServiceType(self):
        SERVICE_TYPE = self.document_type_id.name.getServiceType()
        # if self.document_type_id.name.getCode() in [1]: 
        #     SERVICE_TYPE = 'ServicioFacturacionCompraVenta'
        # if self.document_type_id.name.getCode() in [17]:
        #     if self.company_id.getL10nBoCodeModality() == '1':
        #         SERVICE_TYPE = 'ServicioFacturacionElectronica'
        #     elif self.company_id.getL10nBoCodeModality() == '2':
        #         SERVICE_TYPE = 'ServicioFacturacionComputarizada'
        #raise UserError(SERVICE_TYPE)
        return SERVICE_TYPE
    
    def getModalityType(self):
        return self.document_type_id.name.getModalityType()
    
    
    

    def send_invoice(self):
        if self.document_type_id and self.move_type in ['out_invoice', 'out_refund']:
            # SERVICIOS DE RECEPCION
            WSDL_RESPONSE = False
            if self.document_type_id.name.getCode() in self.getAvailableDocument(): 
                SERVICE_TYPE = self.getServiceType()
                MODALITY_TYPE = self.getModalityType()
                METHOD = self.getReceptionMethod()
                
                # if self.document_type_id.name.getCode() in [3]:
                #     #SERVICE_TYPE = 'ServicioFacturacionElectronica'
                #     MODALITY_TYPE = self.company_id.getL10nBoCodeModality()
                
                # if self.document_type_id.name.getCode() in [24, 47, 48]: # /|\ ADD MORE DOCUMENTS
                #     WSDL_RESPONSE = self.soap_service(METHOD='recepcionDocumentoAjuste', SERVICE_TYPE=SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
                # else:
                WSDL_RESPONSE = self.soap_service(METHOD=METHOD, SERVICE_TYPE=SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
                
                    
            if WSDL_RESPONSE:
                self.post_process_soap_siat(WSDL_RESPONSE)
            


    def post_process_soap_siat(self, res):
        self.write({'success': res.get('success')})
        if self.success:

            res_data = res.get('data', {})
            if res_data:
                self.write(
                    {
                        'edi_state' : res_data.codigoDescripcion,
                        'codigoEstado' : res_data.codigoEstado,
                        'codigoRecepcion' : res_data.codigoRecepcion,
                        'transaccion' : res_data.transaccion
                    }
                )
                #if not self.transaccion:
                #    raise UserError(res_data.codigoDescripcion)
                
            self.setMessageList(res_data.mensajesList)
        
        try:
            
            self.write({'error' : res.get('error')})
        except:
            pass

    def setMessageList(self, _lists):
        while self.messagesList_ids:
            self.messagesList_ids[0].unlink()
        for _list in _lists:
            self.messagesList_ids.create({'name' : fields.datetime.now(), 'code': _list.codigo, 'description': _list.descripcion, 'account_move_id': self.id  })
            
    
    def check_partner_id(self):
        for record in self:
            if not record.force_send:    
                if record.pos_id and record.pos_id.getEmisionCode() == 1:
                    if record.partner_id.getNit() in ['99001', '99002', '99003']:
                        record.write({'force_send': True})
                        
                    elif self.partner_id.getIdentificationCode() == 5 and int(self.getPartnerNit()) != 0 and record.partner_id.nit_state in ['NIT INEXISTENTE', 'NIT INACTIVO'] and not record.force_send:
                        raise UserError(record.partner_id.nit_state)
                else:
                    record.write({'force_send': True})
            if not record.partner_id.email:
                record.partner_id.write({'email': record.company_id.email })

    def getInvoiceNumber(self):
        return int(self.invoice_number)

    def generateCuf(self):
        _logger.info('GENERACION DEL CUF:')
        nit = self.company_id.getNit()
        nit = '0' * (13-len(nit)) + nit
        _logger.info(f'NIT : {nit}')

        fechaHora = self.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz'))
        fechaHora = self.getFechaHoraCuf(fechaHora.strftime("%Y%m%d%H%M%S%f"))
        _logger.info(f'FECHA Y HORA : {fechaHora}')
        
        sucursal = self.pos_id.branch_office_id.getCode()
        sucursal = '0' * (4-len(str(sucursal))) + str(sucursal)
        _logger.info(f'SUCURSAL : {sucursal}')

        modalidad = self.company_id.getL10nBoCodeModality()
        _logger.info(f'MODALIDAD : {modalidad}')
        

        emision = str(self.pos_id.getEmisionCode())
        _logger.info(f'TIPO EMISION : {emision}')
        
        tipoFactura = str(self.document_type_id.name.invoice_type_id.getCode())
        _logger.info(f'TIPO FACTURA : {tipoFactura}')
        
        docSector = self.document_type_id.getCode()
        docSector = '0' * (2-len(str(docSector))) + str(docSector)
        _logger.info(f'SECTOR : {docSector}')
        
        numeroFactura = '0' * (10-len(str(self.getInvoiceNumber()))) + str(self.getInvoiceNumber())
        _logger.info(f'NRO. FACTURA : {numeroFactura}')
        
        pos = '0' * (4-len(str(self.pos_id.getCode()))) + str(self.pos_id.getCode())
        _logger.info(f'POS : {pos}')
        
        cadena = nit + fechaHora + sucursal + modalidad + emision + tipoFactura + docSector + numeroFactura + pos
        _logger.info(f'CONCATENADO : {cadena}')
        codAutoverificador = calculaDigitoMod11(cadena, 1, 9, False)
        cadena += str(codAutoverificador)
        _logger.info(f'MODULO 11 : {cadena}')

        _base16 = Base16(cadena) + self.pos_id.getControlCode()
        _logger.info(f'BASE 16 : {_base16}')
        return _base16
    
    def getFechaHoraCuf(self, date):
        fechaHora = ''
        if len(date) < 17:
            fechaHora = '0' * (17-len(date)) + date
        elif len(date) == 17:
            fechaHora = date
        elif len(date) > 17:
            for i in range(0,17):
                fechaHora += date[i]
        return fechaHora

    def str_edi_format(self):
        provider_modality = self.company_id.getL10nBoCodeModality()
        _str = ''
        if provider_modality == '1':
            _logger.info('FORMATO DE FACTURACION ELECTRONICA')
            _str = self.edi_format_electronic()
        elif provider_modality == '2':
            _logger.info('FORMATO DE FACTURACION COMPUTARIZADA')
            _str = self.edi_format_computerzed()
        return _str
    
    def edi_format_electronic(self):
        self.ensure_one()
        values = self.generate_electronic_format_srt()
        values = values.encode('utf-8')
        return values
    
    def generate_electronic_format_srt(self):
        _str = ''
        if self.document_type_id:
            if self.document_type_id.getCode() == 1:
                _str = self.purchase_sale_format_electronic()    
            elif self.document_type_id.getCode() == 24:
                _str = self.credit_debit_note_format_electronic()    
            elif self.document_type_id.getCode() == 47:
                _str = self.credit_debit_note_discount_format_electronic()    
            elif self.document_type_id.getCode() == 48:
                _str = self.credit_debit_note_ice_format_electronic()    
            
            # others...
        return _str
    
    def edi_format_computerzed(self):
        self.ensure_one()
        values = self.generate_computerized_format_str()
        values = values.encode('utf-8')
        return values
    
    def generate_computerized_format_str(self) -> str:
        _str = ''
        if self.document_type_id:
            if self.document_type_id.getCode() == 1:
                _str = self.purchase_sale_format_computerized()
            elif self.document_type_id.getCode() == 24:
                _str = self.credit_debit_note_format_computerized()

            elif self.document_type_id.getCode() == 47:
                _str = self.credit_debit_note_discount_format_computerized()
            # elif self.document_type_id.getCode() == 48:
            #     _str = self.credit_debit_note_ice_format_computerized()
            
            #others...
        return _str
    

    def getAmountEffective(self):
        return self.roundingUp(self.getAmountOnIva() * 0.13, self.decimalbo())
    # CALCS
    def amountCurrency(self):
        amount_total = self.getAmountTotal() / self.currency_id.getExchangeRate() #self.tax_totals.get('amount_total', 0.00)# / self.currency_id.getExchangeRate()
        return self.roundingUp(amount_total, self.decimalbo()) #round(amount_total - self.amount_giftcard,2)
    
    def AmountProrated(self):
        return self.roundingUp(sum([line.get_prorated_line_discount() for line in self.get_invoice_lines()]), self.decimalbo())
        

    def getAmountSubTotal(self):
        amount_subtotal = sum([ self.roundingUp(line.getSubTotal(), self.decimalbo()) for line in self.get_invoice_lines()])
        return self.roundingUp(amount_subtotal, self.decimalbo())
        

    def getAmountTotal(self) -> float :
        amount_total = self.getAmountSubTotal() #sum([line.getSubTotal() for line in self.get_invoice_lines()])
        amount_total -= self.getAmountDiscount()
        amount_total -= self.AmountProrated()
        return self.roundingUp(amount_total, self.decimalbo())
        
    
    def getAmountOnIva(self) -> float:
        if self.document_type_id.name.invoice_type_id.getCode() != 2: # SOLO DOCUMENTOS DIFERENTES A "SIN CREDITO FISCAL"
            amount = self.roundingUp(self.getAmountTotal() - self.getAmountGiftCard(),2)
            return amount
        return 0
    

    def getAmountOnIvaExchageRate(self):
        return round(self.getAmountOnIva() / self.currency_id.getExchangeRate(), 2 )
        
    @api.model
    def get_xsd_path(self):
        xsd_name = None
        provider_modality = self.company_id.getL10nBoCodeModality()
        if self.document_type_id:
            if provider_modality == '1':
                if self.document_type_id.getCode() == 1:
                    pass#xsd_name = 'facturaElectronicaCompraVenta.xsd'
                # ... AD MORE XSD PATHS

            elif provider_modality == '2':
                if self.document_type_id.getCode() == 1:
                    xsd_name = 'facturaComputarizadaCompraVenta.xsd'
                # ... AD MORE XSD PATHS
                #if self.document_type_id.getCode() == 17:
                #    xsd_name = 'facturaComputarizadaHospitalClinica.xsd'
                #if self.document_type_id.getCode() == 48:
                #    xsd_name = 'notaComputarizadaCreditoDebitoIce.xsd'
                
        if xsd_name:
            return os.path.join(os.path.dirname(__file__), f'../templates/{xsd_name}')
        return False

    def validate_xml(self, xml_str, xsd_path):
        if xml_str and xsd_path:
            try:
                with open(xsd_path, 'rb') as xsd_file:
                    xmlschema_doc = etree.parse(xsd_file)
                    xmlschema = etree.XMLSchema(xmlschema_doc)
                    
                parser = etree.XMLParser(recover=True)
                xml_doc = etree.fromstring(xml_str.encode('utf-8'), parser)

                if not xmlschema.validate(xml_doc):
                    # Obtener los errores de validación
                    log = xmlschema.error_log
                    error_details = "\n".join([f"Linea {error.line}: {error.message}" for error in log])
                    raise ValidationError(f"El XML no es válido según el esquema XSD proporcionado.\nErrores:\n{error_details}")
            except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
                raise ValidationError(f"Error al analizar el XML o el esquema XSD: {str(e)}")
            except IOError as e:
                raise ValidationError(f"No se pudo leer el archivo XSD: {str(e)}")
            

    def get_cafc_id(self, get_code = False, get_sequence = False):
        cafc_id = False
        cafc_ids =  self.document_type_id.name.cafc_ids #self.env['l10n.bo.cafc'].search([('branch_office_id','=',self.branch_office_id.id)])
        if cafc_ids:
            cafc_id = self.getCafcForEconomicActivity(cafc_ids)
            if cafc_id:
                #cafc_id.validateDocumentSector(self.document_type_id)
                if get_code:
                    return cafc_id.getCode()
                if get_sequence:
                    sequence = cafc_id.actual_sequence
                    cafc_id.next_sequence()
                    return sequence
        raise UserError(f"No se encontro CAFC's vinculados al documento")
        
    def getCafcForEconomicActivity(self, cafc_ids = False):
        find = False
        cafc_find_id = False
        economic_activity = self.get_enconomic_activities_in_invoice_line()
        for cafc_id in cafc_ids:
            if cafc_id.all_activities_inside(economic_activity):
                if not find:
                    find = True
                    cafc_find_id = cafc_id
                else:
                    raise UserError(f'Se encontro mas un codigo CAFC para las activiad economica asociada: {economic_activity}')
        if not find:
            raise UserError(f'No se encontro un codigo CAFC para la activiad economica asociada: {economic_activity}')
        
        return cafc_find_id

    def get_enconomic_activities_in_invoice_line(self, mark_invoice = False)->dict:
        economic_activities = []
        for line in self.get_invoice_lines():
            economic_activities.append(line.product_id.getAe())
        if economic_activities:
            economic_activities = set(economic_activities)
            economic_activities = list(economic_activities)
            if len(economic_activities) > 1:
                raise UserError(f'Se encontro multiples actividades en la factura, solo se permite validar una factura por actividad economica, actividades detectadas: {economic_activities}')
        if mark_invoice and economic_activities:
            ae = self.env['l10n.bo.activity'].search([('codigoCaeb','=',economic_activities[0])], limit=1)
            if ae:
                self.write({'economic_activity_id' : ae.id})
            else:
                raise UserError(f'No se encontro el codigo: {economic_activities[0]}, en la base de datos Odoo')
        return economic_activities
        
    
    def get_legend_default(self, _global = False):
        legends = self.env['l10n.bo.legend.code'].search([])
        if _global:
            if self.economic_activity_id:
                legends = legends.filtered(lambda legend: legend.codigoActividad == self.economic_activity_id.codigoCaeb)
        return legends[random.randint(0,len(legends)-1)].id if legends else False
        #return False
    

    def item_number_assigned(self):
        for record in self:
            if record.move_type == 'out_invoice':
                item = 1
                for line in record.get_invoice_lines():
                        line.write({'item_number':item})
                        item += 1

    
    @api.model
    def roundingUp(self, value, precision):
        #factor = 10 ** precision
        #return (value * factor + 0.5) // 1 / factor
        return float(Decimal(str(value)).quantize(Decimal('1.' + '0' * precision), rounding=ROUND_HALF_UP))
    
    

    def getIdentificationCode(self):
        if self.identification_type_id:
            return self.identification_type_id.getCode()
        return self.partner_id.getIdentificationCode()
    

    def get_logo_style(self):
        """Retorna el estilo CSS para el logo basado en el tamaño definido."""
        size = 150 # px
        if self.pos_id.logo_size:
            size += ((int(self.pos_id.logo_size))/100)*size
        return f'width: {size}px; height: auto;'
    
    def get_company_data_style(self):
        """Retorna el estilo CSS para el logo basado en el tamaño definido."""
        align = 'center'
        width = 65
        if self.pos_id.logo_position in ['left', 'right']:
            #align = 'left'
            width = 55
            

        return f'text-align: {align}; width: {width}%;'
    


    def get_invoice_lines(self): # Lineas de factura
        invoice_line_ids = self.invoice_line_ids.filtered( 
            lambda line : \
                line.display_type == 'product' and \
                not line.product_id.gif_product
        )
        return invoice_line_ids
    

    def getItemLine(self, ITEM):
        for line in self.get_invoice_lines():
            if line.getItemNumber() == ITEM:
                return line
        return False