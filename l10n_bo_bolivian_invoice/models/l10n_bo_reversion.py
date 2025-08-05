# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    reversion = fields.Boolean(
        string='Factura revertida',
        copy=False,
        readonly=True
    )
    

    def action_reversion(self):
        if not self.reversion:
            SERVICE_TYPE = self.getServiceType()
            MODALITY_TYPE = None
                    
            if self.document_type_id.name.getCode() in [3]:
                        #SERVICE_TYPE = 'ServicioFacturacionElectronica'
                        MODALITY_TYPE = self.company_id.getL10nBoCodeModality()
                    
            if self.move_type == 'out_invoice':
                WSDL_RESPONSE = self.soap_service(METHOD='reversionAnulacionFactura', SERVICE_TYPE= SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
            elif self.move_type == 'out_refund':
                WSDL_RESPONSE = self.soap_service(METHOD='reversionAnulacionDocumentoAjuste', SERVICE_TYPE= 'ServicioFacturacionDocumentoAjuste')
                 
            _logger.info(f"{WSDL_RESPONSE}")
            self.post_revercion_process_soap_siat(WSDL_RESPONSE)

            if self.reversion:
                self.button_draft()
                if self.state=="draft":
                    self.action_post()
        else:
            raise UserError(f"El Nro. Factura {self.getInvoiceNumber()}, registro: {self.name}, ya fue revertido anteriormente.")
             

    def reversionAnulacionFactura(self, WSDL_SERVICE):
        _params = self._prepare_invoice_reversion_params_soap()
        WSDL = WSDL_SERVICE.getWsdl()
        _logger.info(f"Parametros revercion : {_params}, WSDL: {WSDL}")
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, _params, 'reversionAnulacionFactura')
        return WSDL_RESPONSE

    def reversionAnulacionDocumentoAjuste(self, WSDL_SERVICE):
        _params = self._prepare_invoice_reversion_params_soap()
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, _params, 'reversionAnulacionDocumentoAjuste')
        return WSDL_RESPONSE
         

    def _prepare_invoice_reversion_params_soap(self):
        _name_field = None
        if self.document_type_id.name.invoice_type_id.getCode() in [1,2]:
            _name_field = 'SolicitudServicioReversionAnulacionFactura'
        elif  self.document_type_id.name.invoice_type_id.getCode() == 3: 
            _name_field = 'SolicitudServicioReversionAnulacionDocumentoAjuste'
        request_data = {
            _name_field: {
                'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
                'codigoPuntoVenta': int(self.pos_id.getCode()),
                'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                'codigoSucursal': self.pos_id.branch_office_id.getCode(),
                'nit': self.company_id.getNit(),
                'codigoDocumentoSector': self.document_type_id.getCode(),
                'codigoEmision': self.pos_id.getEmisionCode(),
                'codigoModalidad': int(self.company_id.getL10nBoCodeModality()),
                'cufd': self.pos_id.getCufd(),
                'cuis': self.pos_id.getCuis(),
                'tipoFacturaDocumento': self.document_type_id.name.invoice_type_id.getCode(),
                'cuf': self.cuf
            }
        }
        return request_data
    
    def post_revercion_process_soap_siat(self, res):
        self.write({'success': res.get('success')})
        if self.success:

            res_data = res.get('data', {})
            if res_data:
                self.write(
                    {
                        'edi_state' : res_data.codigoDescripcion,
                        'codigoEstado' : res_data.codigoEstado,
                        'codigoRecepcion' : res_data.codigoRecepcion,
                        'reversion' : res_data.transaccion
                    }
                )
            self.setMessageList(res_data.mensajesList)
        if self.success == False:
            self.write({'error' : res.get('error')})