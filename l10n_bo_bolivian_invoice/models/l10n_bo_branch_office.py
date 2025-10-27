# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class L10nBoBranchOffice(models.Model):
    _name = 'l10n.bo.branch.office'
    _description = 'Sucursales'

    
    name = fields.Char(
        string='Nombre',
        copy=False,
        readonly=True 
    )
    
    
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company',
        required=True
    )

    
    country_id = fields.Many2one(
        string='Pais',
        comodel_name='res.country',
        related='company_id.country_id',
        readonly=True,
        store=True
    )
    

    state_id = fields.Many2one(
        string='Departamento',
        comodel_name='res.country.state'
    )

    province_id = fields.Many2one(
        string='Provincia',
        comodel_name='res.city',
        copy=False
    )

    municipality_id = fields.Many2one(
        string='Municipio',
        comodel_name='res.municipality',
        copy=False
    )    
    
    phone = fields.Char(
        string='Telefono',
    )
    
    def getPhone(self):
        return self.phone or self.company_id.partner_id.getPhone()
    
    def getMunicipalityName(self):
        if self.municipality_id:
            return self.municipality_id.name
        else:
            return self.company_id.getMunicipalityName()

    _sql_constraints = [
        ('unique_code_company',
        'unique(company_id, code)',
        'El código de sucursal ya existe para esta empresa.')
    ]


    # @api.model
    # def create(self, vals):
    #     existing_record = self.search([('company_id', '=', vals.get('company_id'),('code','=',vals.get('code')))])
    #     if existing_record:
    #         raise ValidationError('Ya existe un registro para esta compañía.')
        
    #     res = super(L10nBoBranchOffice, self).create(vals)
    #     return res
    
    @api.constrains('company_id')
    def _check_company_id(self):
        for record in self:
            company_id = record.company_id.id if record.company_id else False
            for pos_id in record.l10n_bo_pos_ids:
                pos_id.write({'company_id' : company_id})
        
    
    
    code = fields.Integer(
        string='Código',
        required=True,
        copy=False
    )

    
    @api.constrains('code')
    def _check_code(self):
        for record in self:
            record.write(
                {
                    'name' : 'CASA MATRIZ' if record.code == 0 else 'Sucursal '+str(record.code)
                }
            )

   
    # ELIMINAR CAMPO
    address = fields.Text(
        string='Dirección',
        copy=False
    )

    
    pos_id = fields.Many2one(
        string='POS Inicio de sistema',
        comodel_name='l10n.bo.pos',
    )


    default_pos_id = fields.Many2one(
        string='Punto de venta predeterminado',
        comodel_name='l10n.bo.pos',
    )

    


    l10n_bo_pos_ids = fields.One2many(
        string='Puntos de venta',
        comodel_name='l10n.bo.pos',
        inverse_name='branch_office_id', 
        copy=False
    )

    
    def getCode(self):
        return self.code
    
    
    def update_pos_from_siat(self):
        pos = self.pos_id
        if pos and pos.getCuis():
            connection = self.soap_service(METHOD='verificarComunicacion')
            if connection:
            #if self.soap_service('verificarComunicacion','FacturacionOperaciones'):
                res = self.soap_service('consultaPuntoVenta')
                _logger.info(f"{res}")
                self.createPosS(res)
            else:
                return self.showMessage( 'Error de sincronizacion', 'Sin coneccion con la base de datos del SIN' )
        else:
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Respuesta',
                    'message': 'Debe registrar y obtener el cuis del Punto de venta 0, en primera instancia',
                    'sticky': False,
                }
            }
    
    def consultaPuntoVenta(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': int(self.company_id.getL10nBoCodeEnvironment()),
            'codigoSucursal': self.code,
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'cuis': self.pos_id.getCuis(),
        }
        OBJECT = {'SolicitudConsultaPuntoVenta': PARAMS}
        #WSDL = WSDL_SERVICE.getWsdl()
        #_logger.info(f'WSDL: {WSDL}')
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(TOKEN, OBJECT)
        return WSDL_RESPONSE
    

    def createPosS(self, res):
        if res.get('success', False):
            res_data = res.get('data',{})
            if res_data:
                if res_data.transaccion:
                    for pos in res_data.listaPuntosVentas:
                        pos_id = self.l10n_bo_pos_ids.filtered( lambda p : p.code ==  pos.codigoPuntoVenta)  #self.env['l10n.bo.pos'].search([('code','=',pos.codigoPuntoVenta)], limit=1)
                        if not pos_id:
                            type_id = self.env['l10n.bo.type.point.sale'].search([('descripcion','=',pos.tipoPuntoVenta)], limit=1)

                            self.l10n_bo_pos_ids.create(
                                {
                                    'code' : pos.codigoPuntoVenta,
                                    'pos_type_id' : type_id.id if type_id else False,
                                    'branch_office_id' : self.id,
                                    'transaccion' : True,
                                    'active' : True
                                }
                            )
                else:
                    pass

    
    def cuis_massive_request(self):
        if self.soap_service('verificarComunicacion','FacturacionCodigos'):
            res = self.soap_service('cuisMasivo')
            if res.get('success', False):
                res_data = res.get('data',{})
                if res_data and res_data.transaccion:
                    listaRespuestasCuis = res_data.listaRespuestasCuis
                    for RespuestasCuis in listaRespuestasCuis:
                        pos_id = self.l10n_bo_pos_ids.filtered(lambda pos: pos.code == RespuestasCuis.codigoPuntoVenta)
                        if pos_id:
                            pos_id.cuis_id.prepare_wsdl_reponse({'success': True, 'data': RespuestasCuis})
        else:
            return self.showMessage( 'Error de sincronizacion', 'Sin coneccion con la base de datos del SIN' )
    
    def cuisMasivo(self, WSDL_SERVICE):
        codigo_pos_list = []

        for pos_id in self.l10n_bo_pos_ids:
                codigo_pos_list.append({
                    'codigoPuntoVenta': pos_id.getCode(),
                    'codigoSucursal': self.getCode(),
                })

        PARAMS = {
            'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
            'codigoModalidad': self.company_id.getL10nBoCodeModality(),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'datosSolicitud': codigo_pos_list,
        }

        OBJECT = {'SolicitudCuisMasivoSistemas': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        _logger.info(f'WSDL: {WSDL}')
        _logger.info(f'DATOS DE SOLICITUD: {PARAMS}')
        
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'cuisMasivo')
        return WSDL_RESPONSE
    
    def cufdMasivo(self, WSDL_SERVICE):
        PARAMS = {
            'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
            'codigoModalidad': self.company_id.getL10nBoCodeModality(),
            'codigoSistema': self.company_id.getL10nBoCodeSystem(),
            'nit': self.company_id.getNit(),
            'datosSolicitud': [
                {
                    'codigoPuntoVenta': pos_id.getCode(),
                    'codigoSucursal': self.getCode(),
                    'cuis': pos_id.getCuis()
                }
                for pos_id in self.l10n_bo_pos_ids if pos_id.getCuis() and pos_id.getEmisionCode() == 1
            ],
        }
        OBJECT = {'SolicitudCufdMasivo': PARAMS}
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'cufdMasivo')
        return WSDL_RESPONSE
    
    def showMessage(self, title, body):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'{title}',
                'message': f'{body}',
                'sticky': False,
            }
        }


    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].soap_service(METHOD, self.company_id.getL10nBoCodeEnvironment())
        if WSDL_SERVICE:
            return getattr(self, METHOD)(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')
    
        # PARAMS = [
        #         ('name','=',METHOD),
        #         ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        # ]
        # if SERVICE_TYPE:
        #     PARAMS.append(('service_type','=', SERVICE_TYPE))

        # WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        # if WSDL_SERVICE:
        #     WSDL_RESPONSE = getattr(self, METHOD)(WSDL_SERVICE)
        #     return WSDL_RESPONSE
        # raise UserError(f'Servicio: {METHOD} no encontrado')
    
    def pos_system_init(self, reload = False):
        pos_id = self.l10n_bo_pos_ids.filtered(lambda pos: pos.code == 0)[:1]
        if pos_id:
            self.write({'pos_id': pos_id[0].id})
        else:
            if not reload:
                self.l10n_bo_pos_ids.create({'code':0, 'branch_office_id': self.id})
                self.pos_system_init(True)
            else:
                raise UserError('Error al iniciar Punto de venta de inicio de sistema')
    
    def cufd_massive_request(self):
        if self.l10n_bo_pos_ids.filtered(lambda pos: pos.emision_code == 1 and pos.getCuis()):
            if not self.pos_id:
                self.pos_system_init()
            if self.pos_id:
                res = self.soap_service('cufdMasivo')
                if res.get('success', False):
                    res_data = res.get('data',{})
                    if res_data and res_data.transaccion:
                        listaRespuestasCufd = res_data.listaRespuestasCufd
                        for RespuestasCufd in listaRespuestasCufd:
                            pos_id = self.l10n_bo_pos_ids.filtered(lambda pos: pos.code == RespuestasCufd.codigoPuntoVenta)
                            if pos_id:
                                pos_id.cufd_id.prepare_wsdl_reponse({'success': True, 'data': RespuestasCufd})

    
    
    def test_server_cominication(self):
        raise UserError(self.soap_service('verificarComunicacion','FacturacionOperaciones'))
    
    def verificarComunicacion(self, WSDL_SERVICE):
        response = WSDL_SERVICE.process_soap_siat(token = self.company_id.getDelegateToken())
        if response.get('success', False):
            res_data = response.get('data')
            if res_data.transaccion:
                return True
        return False

        # WSDL = WSDL_SERVICE.getWsdl()
        # TOKEN = self.company_id.l10n_bo_delegate_token
        # response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, {},  'verificarComunicacion')
        # _logger.info(f"{response}")
        # if response.get('success', False):
        #     res_data = response.get('data')
        #     if res_data.transaccion:
        #         for obs in res_data.mensajesList:
        #             if obs.codigo == 926:
        #                 return True
        #     return False
        # else:
        #         return False
        

    def action_pos_register_wizard(self):
        return {
            'name': 'Solicitud de registro de punto de venta (BO)',
            'type': 'ir.actions.act_window',
            'res_model': 'l10n.bo.pos.register.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_branch_office_id': self.id, 
                'default_pos_id': self.pos_id.id
            }
        }