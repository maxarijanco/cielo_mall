# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)




class L10nBoVerify(models.Model):
    _inherit = ['account.move']
    
    def getVerificationMethod(self):
        return self.document_type_id.name.getVerificationMethod()

    def verificacionEstadoFactura(self):
        METHOD = self.getVerificationMethod() #'verificacionEstadoFactura'
        SERVICE_TYPE = self.getServiceType()
        MODALITY_TYPE = self.getModalityType()
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
            WSDL = WSDL_SERVICE.getWsdl()
            _logger.info(f'WSDL: {WSDL}')
            TOKEN = self.company_id.getDelegateToken()
            OBJECT = {
                self.env['l10n.bo.type.invoice'].getObjectName(METHOD): #'SolicitudServicioVerificacionEstadoFactura':
                {
                    'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
                    'codigoPuntoVenta': int(self.pos_id.getCode()),
                    'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                    'codigoSucursal': self.pos_id.branch_office_id.getCode(),
                    'nit': self.company_id.getNit(),
                    'codigoDocumentoSector': self.getDocumentSector(),
                    'codigoEmision': 1,
                    'codigoModalidad': int(self.company_id.getL10nBoCodeModality()),
                    'cufd': self.pos_id.getCufd(True),
                    'cuis': self.pos_id.getCuis(),
                    'tipoFacturaDocumento': self.document_type_id.name.invoice_type_id.getCode(),
                    'cuf': self.cuf
                }
            }
            _logger.info(f"PARAMETROS: {OBJECT}")
            response = WSDL_SERVICE.process_soap_siat(TOKEN, OBJECT)
            _logger.info(f"RESPUESTA: {response}")
            if response.get('success', False):
                res_data = response.get('data')
                if res_data.transaccion:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'info',
                            'title': 'Verificación exitosa',
                            'message': f"""ESTADO: {res_data.codigoDescripcion} \
                                CODIGO: {res_data.codigoRecepcion}""",
                            'sticky': False,
                        }
                    }
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': 'Verificación fallida',
                        'message': 'Factura no verificada',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Verificación fallida',
                        'message': f"{response.get('error', False)}",
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        raise UserError(f'Servicio: {METHOD} no encontrado')