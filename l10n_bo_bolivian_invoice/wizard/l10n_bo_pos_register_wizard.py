# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError



import logging
_logger = logging.getLogger(__name__)



class L10nBoPOSRegisterWizard(models.TransientModel):
    _name = 'l10n.bo.pos.register.wizard'
    _description = 'Solicitud de Registro de punto de venta'

    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        required=True
    )

    
    pos_id = fields.Many2one(
        string='POS Inicio de sistema',
        comodel_name='l10n.bo.pos',
        related='branch_office_id.pos_id',
        readonly=True,
        store=True,
        required=True
    )
    

    
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        related='branch_office_id.company_id',
        readonly=True,
    )
    
    
    pos_type_id = fields.Many2one(
        string='Tipo',
        comodel_name='l10n.bo.type.point.sale',
        required=True
    )

    description = fields.Text(
        string='Descripción',
        help='Descripción del punto de venta. (OPCIONAL)'
    )

    name = fields.Char(
        string='Referencia',
        help='Nombre que le asignará a su punto de venta.',
        required=True
    )

    
    transaccion = fields.Boolean(
        string='transaccion',
    )
    
    # error = fields.Text(
    #     string='error',
    # )
    
    
    
    
    

    def registroPuntoVenta(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoModalidad' : int(self.company_id.getL10nBoCodeModality()),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'codigoSucursal': self.branch_office_id.getCode(),
            'codigoTipoPuntoVenta' : str(self.pos_type_id.getCode()) if self.pos_type_id else False,
            'cuis': self.pos_id.getCuis(),
            'descripcion' : self.description,
            'nit': self.company_id.getNit(),
            'nombrePuntoVenta' : self.name
        }
        OBJECT = {'SolicitudRegistroPuntoVenta': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        _logger.info(f'WSDL: {WSDL}')
        _logger.info(f'PARAMETROS: {OBJECT}')
        
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'registroPuntoVenta')
        return WSDL_RESPONSE


    def open_pos_request(self):
        res = self.soap_service('registroPuntoVenta')
        _logger.info(f"{res}")
        response = {'success' : False, 'msgs' : False, 'code': False}
        if res.get('success', False):
            res_data = res.get('data', {})
            if res_data.transaccion:
                self.write({'transaccion': res_data.transaccion})
                response['success'] = True
                response['code'] = res_data.codigoPuntoVenta
            if res_data.mensajesList:
                response['msgs'] = self.process_message_list(res_data.mensajesList)
        elif res.get('error', False):
            response['msgs'] = {'title' : 'ERROR', 'body' : res['error'] }
        return response
        
        
    
    

    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')
    


    def button_action_pos_register(self):
        res = self.open_pos_request()
        if res['msgs']:
            return self.showMessage(msg_list=res['msgs'])
        if res['success']:
            DISPLAY = {'type': 'ir.actions.act_window_close'}
            if res['code']:
                DISPLAY = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': f"Codigo punto de venta: {res['code']}.\nCreado.",
                        'sticky': True,
                        'next': DISPLAY,
                    }
                }
            return DISPLAY
        return {'type': 'ir.actions.act_window_close'}
        
        
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    
    def showMessage(self, title = False, body = False, msg_list: dict = None):
        if title or body:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': title or 'Mensaje',
                    'message': body or 'Mensaje',
                    'sticky': False,
                    'next': False
                }
            }

        if not msg_list:
            return False

        result = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'title': msg_list.get('title'),
                'message': msg_list.get('body'),
                'sticky': False,
                'next': False
            }
        }

        if msg_list:
            result['params']['next'] = self.showMessage( msg_list=msg_list.get('next', {}) )

        return result

    
    def process_message_list(self, msg_list) -> dict:
        if not msg_list:
            return {}

        return {
            'title': msg_list[0].codigo,
            'body': msg_list[0].descripcion,
            'next' : self.process_message_list(msg_list[1:])

        }

    
    def test_siat_connection(self):
        return self.pos_id.test_siat_connection()