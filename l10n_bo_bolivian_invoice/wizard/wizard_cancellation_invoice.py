# -*- coding: utf-8 -*-

from odoo import api, models, fields

from odoo.exceptions import UserError


class WizardCancellationInvoice(models.TransientModel):
    _name = 'wizard.cancellation.invoice'
    _description = 'Anulacion manual de facturas'

    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos'
    )
    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office'
    )
    
    
    company_id = fields.Many2one(
        string='Compañia',
        comodel_name='res.company',
        related='branch_office_id.company_id',
        readonly=True,
        store=True
        
    )
    
    
    
    
    document_type_id = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.document.type'
    )


    invoice_type_id = fields.Many2one(
        string='Tipo factura',
        comodel_name='l10n.bo.type.invoice',
        related='document_type_id.invoice_type_id',
        readonly=True,
        store=True
    )
    
    
    
    
    reason_id = fields.Many2one(
        string='Motivo',
        comodel_name='l10n.bo.cancellation.reason'
    )
    
    cuf = fields.Char(
        string='cuf',
    )
    
    def action_done(self):
        return self.action_process()
        
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


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
            return getattr(self, f"{METHOD}")(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')
    
    def action_process(self):
        SERVICE_TYPE = self.document_type_id.getServiceType()
        MODALITY_TYPE = self.document_type_id.getModalityType()

        if self.invoice_type_id.getCode() in [1,2]:
            WSDL_RESPONSE = self.soap_service(METHOD='anulacionFactura', SERVICE_TYPE= SERVICE_TYPE, MODALITY_TYPE = MODALITY_TYPE)
        else:
            WSDL_RESPONSE = self.soap_service(METHOD = 'anulacionDocumentoAjuste', SERVICE_TYPE='ServicioFacturacionDocumentoAjuste')
        return self.process_response(response=WSDL_RESPONSE)

    def process_response(self, response):
        if response.get('success', False):
            res_data = response.get('data')
            if res_data:
                msg_list = [ message.descripcion for message in res_data.mensajesList ] if res_data.mensajesList else ''
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'info',
                        'title': 'RESPUESTA',
                        'message': f'{res_data.codigoDescripcion} | {msg_list}',
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'}
                    }
                }
        return {'type': 'ir.actions.act_window_close'}
        


    def params(self):
        return {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoPuntoVenta': int(self.pos_id.getCode()),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'codigoSucursal': self.branch_office_id.getCode(),
            'nit': self.company_id.getNit(),
            'codigoDocumentoSector': self.document_type_id.getCode(),
            'codigoEmision': 1,
            'codigoModalidad': int(self.company_id.getL10nBoCodeModality()),
            'cufd': self.pos_id.getCufd(True),
            'cuis': self.pos_id.getCuis(),
            'tipoFacturaDocumento': self.invoice_type_id.getCode(),
            'codigoMotivo': self.reason_id.getCode(),
            'cuf': self.cuf
        }

    def anulacionFactura(self, WSDL_SERVICE):
        request_data = {
            'SolicitudServicioAnulacionFactura' : self.params()
        }
        TOKEN = self.company_id.getDelegateToken()
        return WSDL_SERVICE.process_soap_siat(TOKEN, request_data)
        
    

    def anulacionDocumentoAjuste(self, WSDL_SERVICE):
        request_data = {
            'SolicitudServicioAnulacionDocumentoAjuste': self.params()
        }
        TOKEN = self.company_id.getDelegateToken()
        return WSDL_SERVICE.process_soap_siat(TOKEN, request_data)
        