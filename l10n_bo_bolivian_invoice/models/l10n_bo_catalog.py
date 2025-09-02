# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.l10n_bo_bolivian_invoice.tools.constants import SiatSoapMethod as siatConstant
import logging
from odoo.exceptions import UserError
from datetime import datetime
from pytz import timezone, utc

_logger = logging.getLogger(__name__)



class CatalogRequest(models.Model):
    _name = 'l10n.bo.catalog.request'
    _description = 'Solicitud de catalogos'
    _order = 'id desc'

    
    name = fields.Char(
        string='Nombre',
        store=True,
        compute='_compute_name' 
    )
    
    state = fields.Selection(
        string='Estado',
        selection=[('draft', 'Borrador'),('imperfect','Imperfecto'), ('success', 'Perfecto')],
        default='draft'
    )

    def add_company(self, this_company,add_company):
        for record in self:
            for line in record.catalog_status_ids:
                line.add_company(this_company,add_company)
    
    def quit_company(self, this_company,add_company):
        for record in self:
            for line in record.catalog_status_ids:
                line.quit_company(this_company,add_company)
    
    
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            sufix = 'general'
            if record.company_id:
                sufix = record.company_id.display_name
            record.name =  f"Sincronización - {record.id} - {sufix}" 
    
    catalog_status_ids = fields.One2many(
        comodel_name='l10n.bo.request.catalog.status', 
        string='Sincronizar catalogos',
        inverse_name='request_catalog_id',
        readonly=True 
    )            

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        copy=False
    )

    
    

    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        copy=False,
    )
    

    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
        copy=False, 
    )

    
    @api.onchange('branch_office_id')
    def _onchange_branch_office_id(self):
        self.write({'pos_id' : self.branch_office_id.l10n_bo_pos_ids[0].id if self.branch_office_id else False })
    
    
    
    
    
    def get_catalogs(self):
        for record in self:
            if record.company_id:
                return record.env['l10n.bo.catalog'].search([('discriminate', '=', True)])
            return record.env['l10n.bo.catalog'].search([('discriminate', '=', False)])
    
    def get_l10n_bo_catalog_sync_ids(self):
        for record in self:
            branch_office_id = record.with_company(record.company_id.id).env['l10n.bo.branch.office'].search([], limit=1)
            if branch_office_id:
                record.catalog_status_ids = [(5, 0, 0)]
                catalogs = record.get_catalogs()
                items = []
                for catalog in catalogs:
                    items.append([
                            0, 0, {
                                'catalog_id': catalog.id,
                                'state': 'draft',
                            }
                        ]
                    )
                record.catalog_status_ids = items

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

    def test_siat_connection(self):
        if self.verificarComunicacion():
            return self.showMessage('Coneccion exitosa','Coneccion exitosa con el SIAT')
        return  self.showMessage('Coneccion fallida','No se tiene coneccion con la base de datos del SIAT') 
    

    def verificarComunicacion(self):
        company_id = self.company_id or self.env.company
        METHOD = 'verificarComunicacion'
        PARAMS = [
                ('service_type','=','FacturacionSincronizacion'),
                ('name','=',METHOD),
                ('environment_type','=', company_id.getL10nBoCodeEnvironment())
            ]
        _logger.info(f"Parametros de busqueda del servicio {METHOD}:{PARAMS}")
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(
            PARAMS,limit=1
        )
        if WSDL_SERVICE:
            WSDL = WSDL_SERVICE.getWsdl()
            TOKEN = company_id.getDelegateToken()
            response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, {},  METHOD)
            _logger.info(f"{response}")
            if response.get('success', False):
                res_data = response.get('data')
                if res_data.transaccion:
                    for obs in res_data.mensajesList:
                        if obs.codigo == 926:
                            return True
                return False
            else:
                    return False

        raise UserError(f'Servicio: {METHOD} no encontrado')
        #response = self.cuis_id.soap_service(METHOD)
        #_logger.info(f"{response}")
        #return response
                

    def button_process_all_siat(self, company_id = None):
        self.get_l10n_bo_catalog_sync_ids()
        if self.catalog_status_ids and self.verificarComunicacion():
            self.ensure_one()
            self.write({'state' : 'success'})
            for catalog in self.catalog_status_ids:
                catalog._button_process_siat(company_id, self.pos_id if self.pos_id else None)
                if self.state != 'imperfect' and catalog.state == 'cancel':
                    self.write({'state' : 'imperfect'})

    

    @api.model
    def set_formats(self):
        records = self.env[self._name].search([])
        for record in records:
            for catalog_status_id in record.catalog_status_ids:
                catalog_status_id.set_format()
    

    @api.model # DAILY
    def update_catalogs(self):
        parametric_catalog_id = self.env['l10n.bo.catalog.request'].sudo().search([('company_id','=',False)], limit=1)
        if parametric_catalog_id:
            _logger.info(f"Actualizando catalogo: {parametric_catalog_id.name}")
            parametric_catalog_id.button_process_all_siat()
        else:
            _logger.info("No se encontro un catalogo parametrico")
            
        
        company_ids = self.env['res.company'].sudo().search([('enable_bo_edi','=',True)])
        for company_id in company_ids:
            catalog_id = self.with_company(company_id.id).env['l10n.bo.catalog.request'].search([('company_id','=',company_id.id)], limit=1)
            _logger.info(f"Actualizando catalogo: {catalog_id.name}")
            catalog_id.button_process_all_siat(company_id)
        



    


class L10nBoRequestCatalogStatus(models.Model):
    _name = 'l10n.bo.request.catalog.status'
    _description = 'Estado de solicitud de catalogos'

    catalog_id = fields.Many2one('l10n.bo.catalog', 'Catalogo')
    name = fields.Char('Sevicio SIAT', store=True, compute='_compute_name')
    error = fields.Char('Error', readonly=True)

    def add_company(self, this_company,add_company):
        for record in self:
            record.catalog_id.add_company(this_company,add_company)

    def quit_company(self, this_company,add_company):
        for record in self:
            record.catalog_id.quit_company(this_company,add_company)

    
    @api.depends('catalog_id')
    def _compute_name(self):
        for status in self:
            status.name = status.catalog_id.name

    code = fields.Selection(related='catalog_id.code')
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Sincronizado'), ('cancel', 'Cancelado')], string='Estado', default='draft')
    request_catalog_id = fields.Many2one(comodel_name='l10n.bo.catalog.request', string='Request', ondelete='cascade', copy=False)

    
    
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company',
        related='request_catalog_id.company_id',
        readonly=True,
        store=True
         
    )
    

    def set_format(self):
        for record in self:
            if record.state == 'done':
                record.catalog_id._format()

    def button_process_siat(self):
        if self.request_catalog_id.verificarComunicacion():
            self._button_process_siat(self.company_id, self.request_catalog_id.pos_id)
        else:
            return self.request_catalog_id.showMessage('Coneccion fallida','No se tiene coneccion con la base de datos del SIAT')
    
    def _button_process_siat(self, company_id = None, pos_id = None):
        self._process_siat(company_id, pos_id)
        

    def _prepare_params_soap(self,pos_id = None):
        company_id = self.company_id if self.company_id else self.env.company

        if not pos_id:
            _pos_code = company_id.branch_office_id.l10n_bo_pos_ids[0] if company_id.branch_office_id and company_id.branch_office_id.l10n_bo_pos_ids else 0
        else:
            _pos_code = pos_id
        request_data = {
            'codigoAmbiente': int(company_id.getL10nBoCodeEnvironment()),
            'codigoPuntoVenta': int(_pos_code.getCode()),
            'codigoSistema': company_id.getL10nBoCodeSystem(),
            'codigoSucursal': company_id.branch_office_id.code,
            'cuis': _pos_code.getCuis(),
            'nit': company_id.getNit()
        }
        return {'SolicitudSincronizacion': request_data}
    
    
    transaccion = fields.Boolean(
        string='Transacción',
        copy=False
    )

    def soap_service(self, METHOD = None, SERVICE_TYPE = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        if SERVICE_TYPE:
            PARAMS.append(('service_type','=', SERVICE_TYPE))

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        if WSDL_SERVICE:
            WSDL_RESPONSE = getattr(self, METHOD)(WSDL_SERVICE)
            return WSDL_RESPONSE
        raise UserError(f'Servicio: {METHOD} no encontrado')
    

    def _process_siat(self, company_id = None, pos_id = None):
        #company_id = self.env.company
        if not company_id:
            company_id = self.company_id if self.company_id else self.env.company
        _logger.info(f"Sincronizando: {self.name}")
        
        

        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search([
                ('name','=',self.catalog_id.code),
                ('environment_type','=', company_id.getL10nBoCodeEnvironment())
            ],limit=1)
        if WSDL_SERVICE:

            WSDL = WSDL_SERVICE.getWsdl()
            _logger.info(f'WSDL: {WSDL}')
            TOKEN = company_id.getDelegateToken()
            PARAMS = self._prepare_params_soap(pos_id)
            _logger.info(f'PARAMETROS: {PARAMS}')
            response = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, PARAMS, self.catalog_id.code)
            
            _logger.info(f'{self.catalog_id.code}')
            
            _logger.info(f'RESPUESTA: {response}')
            if response.get('success'):
                res_data = response.get('data', {})
                self.write({'transaccion':res_data.transaccion})
                if self.transaccion:
                    self.catalog_id.create_records(res_data, company_id)
                    
                else:
                    self.write({'error': f'{res_data.mensajesList}'})
            else:
                self.write({'error' : response.get('error')})
            self.write({'state' : 'done' if self.transaccion else 'cancel'})
            return response
        raise UserError(f"No se encontro el servicio: {self.catalog_id.code}, ambiente: {company_id.getL10nBoCodeEnvironment()}")

'''
Creacion del Catalogo de Códigos de Leyendas Facturas
https://siatanexo.impuestos.gob.bo/index.php/implementacion-servicios-facturacion/sincronizacion-codigos-catalogos
'''

"""
Modelo representacion de todos los catalgos: FacturacionSincronizacion
"""

class CatalogRequest(models.Model):
    _name = 'l10n.bo.catalog'
    _description = 'Catalogos'
    name = fields.Char(
        'Nombre', 
        readonly=True 
    )
    code = fields.Selection(
        selection=siatConstant.SYNC_ALL_TUPLE, 
        string='Tipo codigo',
        readonly=True 
    )
    description = fields.Char(
        'Description', 
        readonly=True 
    )
    
    model = fields.Char(
        string='Modelo de actividad',
        readonly=True 
        
    )
    def create_records(self, request, company_id = None):
        self.env[self.model].create_records(request, company_id)

    
    discriminate = fields.Boolean(
        string='Discriminar',
        readonly=True
    )

    
    required_format = fields.Boolean(
        string='Formatear',
        readonly=True
    )
    


    def _format(self):
        for record in self:
            if record.required_format:
                record.env[record.model]._format()

    def add_company(self, this_company,add_company):
        for record in self:
            if record.discriminate:
                _record_ids = record.env[record.model].search([('company_id','=',this_company.id)])
                for _record_id in _record_ids:
                    _record_id.write({'company_ids': [(4, add_company.id, 0)]})
    
    def quit_company(self, this_company,add_company):
        for record in self:
            if record.discriminate:
                _record_ids = record.env[record.model].search([('company_id','=',this_company.id)])
                for _record_id in _record_ids:
                    _record_id.write({'company_ids': [(3, add_company.id, 0)]})
    


class L10nBoActivity(models.Model):
    _name = 'l10n.bo.activity'
    _description = 'Codigos de actividad'
    _order = 'codigoCaeb ASC'

    codigoCaeb = fields.Char(
        string='Codigo CAEB',
        readonly=True 
    )
    descripcion = fields.Char(
        string='Descripcion',
        readonly=True 
    )
    tipoActividad = fields.Char(
        string='Tipo de actividad',
        readonly=True 
    )
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )

    def getCode(self):
        if self.codigoCaeb:
            return self.codigoCaeb
        else:
            raise UserError('La actividad economica no tiene un codigo')

    @api.depends('codigoCaeb', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoCaeb or '', leg.descripcion or '')
    
    def create_records(self, res_data, company_id = None):
        _logger.info(f"Sincronizando catalogo: {self._description}, en: {company_id.name if company_id else self.company_id.name}")
        if not company_id:
            company_id = self.company_id
        for activity in res_data.listaActividades:
            activity_exist = self.search(
                [
                    ('codigoCaeb', '=', activity.codigoCaeb),
                    ('company_id','=', company_id.id)
                ], 
                limit=1
            )
            if activity_exist:
                activity_exist.write(
                    {
                        'tipoActividad' : activity.tipoActividad,
                        'descripcion' : activity.descripcion
                    }
                )
            else:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoCaeb' : activity.codigoCaeb,
                        'descripcion' : activity.descripcion,
                        'tipoActividad' : activity.tipoActividad,
                        'company_id' : company_id.id
                    }
                )

import pytz

class L10nBoDatetime(models.Model):
    _name = 'l10n.bo.datetime'
    _description = 'Fecha de sincronización'
    _order = 'id desc'

    name = fields.Char(
        string='Fecha y hora', 
        readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    def create_records(self, res, company_id = None):
        _logger.info(f"Fecha y hora de actualizacion de catalogos: {res.fechaHora}")
        
        self.create(
            {
                'name': f"{res.fechaHora}"
            }
        )



class L10nBoActivityDocumentSector(models.Model):
    _name = 'l10n.bo.activity.document.sector'
    _description = 'Códigos de Tipo Documento Sector'
    _order = 'codigoDocumentoSector ASC'
    
    codigoActividad = fields.Char(
        string='Codigo de actividad', 
        #readonly=True 
    )
    
    codigoDocumentoSector = fields.Integer(
        string='Codigo documento sector',
        #readonly=True 
    )
    
    tipoDocumentoSector = fields.Char(
        string='Tipo documento sector',
        #readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    
    @api.depends('codigoActividad', 'codigoDocumentoSector', 'tipoDocumentoSector')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s - %s' % (
            leg.codigoActividad or '', leg.codigoDocumentoSector or '', leg.tipoDocumentoSector or '')

    def getCode(self):
        return self.codigoDocumentoSector
    
    def getServiceType(self):    
        if self.getCode() == 1:
            return 'ServicioFacturacionCompraVenta'
        elif self.getCode() in [24, 47]:
            return 'ServicioFacturacionDocumentoAjuste'
        
        # elif self.getCode() in [6, 8,14,17,16]:
        #     if self.company_id.getL10nBoCodeModality() == '1':
        #         return 'ServicioFacturacionElectronica'
        #     elif self.company_id.getL10nBoCodeModality() == '2':
        #         return 'ServicioFacturacionComputarizada'
        
        return False
    
    def requiredModality(self):
        return []
    
    def getModalityType(self):
        if self.getCode() in self.requiredModality():
            return self.company_id.getL10nBoCodeModality()
        return False
    
    

    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        
        for activity in res.listaActividadesDocumentoSector:
            activity_exist = self.search([('codigoDocumentoSector', '=', activity.codigoDocumentoSector),('company_id','=', company_id.id)], limit=1)
            if activity_exist:
                
                activity_exist.write(
                    {
                        'codigoActividad' : activity.codigoActividad,
                        'tipoDocumentoSector' : activity.tipoDocumentoSector
                    }
                )
            else:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'codigoDocumentoSector': activity.codigoDocumentoSector,
                        'tipoDocumentoSector': activity.tipoDocumentoSector,
                        'company_id' : company_id.id
                    }
                )

class LegendCodesInvoices(models.Model):
    _name = 'l10n.bo.legend.code'
    _description = 'Códigos de Leyendas Facturas'
    _order = 'codigoActividad ASC'

    codigoActividad = fields.Char(
        string='Codigo de actividad',
        readonly=True 
    )
    
    descripcionLeyenda = fields.Text(
        string='Leyenda',
        readonly=True 
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )
    
    @api.depends('codigoActividad', 'descripcionLeyenda')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoActividad or '', leg.descripcionLeyenda or '')

    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        for activity in res.listaLeyendas:
            activity_exist = self.search([('codigoActividad','=',activity.codigoActividad), ('descripcionLeyenda', '=', activity.descripcionLeyenda), ('company_id','=', company_id.id) ], limit=1)
            if not activity_exist:
                self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'descripcionLeyenda': activity.descripcionLeyenda,
                        'company_id' : company_id.id
                    }
                )



class MessageService(models.Model):
    _name = 'l10n.bo.message.service'
    _description = 'Códigos de Mensajes Servicios'

    _order = 'codigoClasificador ASC'

    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )
    name = fields.Char(string='Nombre', store=True, compute='_compute_name')

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )



class ProductService(models.Model):
    _name = 'l10n.bo.product.service'
    _description = 'Productos de servicio SIAT'
    _order = 'codigoProducto ASC'
    
    codigoActividad = fields.Char(
        string='Codigo de actividad',
        
    )

    codigoProducto = fields.Integer(
        string='Codigo de producto',
        readonly=True 
    )
    
    descripcionProducto = fields.Text(
        string='Descripcion',
        readonly=True 
    )    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company,
        readonly=True 
    )

    
    
    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )

    
    @api.constrains('company_ids')
    def _check_company_ids(self):
        for record in self:
            for nandina_id in record.manytowmany_nandina_ids:
                nandina_id.write({'company_ids' : record.company_ids})
    
    
    
    
    manytowmany_nandina_ids = fields.Many2many('l10n.bo.product.service.nandina',string="Codigos nandina",readonly=True)
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    def getAe(self):
        return self.codigoActividad
    
    def getCode(self):
        return self.codigoProducto

    @api.depends('codigoActividad', 'codigoProducto', 'descripcionProducto')
    def _compute_name(self):
        for record in self:
            record.name = '%s - %s - %s' % (
            record.codigoActividad or '', record.codigoProducto or '', record.descripcionProducto or '')
    
    def create_records(self, res, company_id = None):
        if not company_id:
            company_id = self.company_id
        
        for activity in res.listaCodigos:
            record_exist = self.search(['&','&',('codigoActividad','=',activity.codigoActividad), ('codigoProducto','=',activity.codigoProducto),('company_id','=', company_id.id)], limit=1)
            if not record_exist:
                record_exist = self.with_company(company_id.id).env[self._name].create(
                    {
                        'codigoActividad': activity.codigoActividad,
                        'codigoProducto': activity.codigoProducto,
                        'descripcionProducto' : activity.descripcionProducto,
                        'company_id' : company_id.id
                    }
                )
            if activity.nandina:
                for nandina in activity.nandina:
                    nandina_id = self.env['l10n.bo.product.service.nandina'].search([('name','=',nandina),('company_id','=', company_id.id)])
                    if not nandina_id:
                        nandina_ids = [registro_id.id for registro_id in record_exist.manytowmany_nandina_ids]
                        nandina_ids.append(self.with_company(company_id.id).env['l10n.bo.product.service.nandina'].create({'name': nandina,'l10n_bo_product_service_id':record_exist.id, 'company_id' : company_id.id}).id)
                        record_exist.write({'manytowmany_nandina_ids': [(6,0,nandina_ids)]})
                        
class ProductServiceNandina(models.Model):
    _name = 'l10n.bo.product.service.nandina'
    _description = 'Codigos de producto servicio nandina'
    
    name = fields.Char(
        string='Nandina',
        readonly=True 
    )

    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    company_ids = fields.Many2many(
        string='Sucursales',
        comodel_name='res.company',
    )
    
    
    l10n_bo_product_service_id = fields.Many2one(
        string='Producto servicio',
        comodel_name='l10n.bo.product.service',
        readonly=True 
    )

    def getCode(self):
        return self.name
    
    
    
    
    

    

class SignificantEvent(models.Model):
    _name = 'l10n.bo.significant.event'
    _description = 'Códigos de Eventos Significativos'
    _order = 'codigoClasificador ASC'
    codigoClasificador = fields.Integer('Codigo')
    descripcion = fields.Text('Descripcion')

    """
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    """
    name = fields.Char('Name', store=True, compute='_compute_name')

    def getCode(self):
        return self.codigoClasificador

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def complete_name(self):
        for leg in self.search([]):
            leg._compute_name()

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class CancellationReason(models.Model):
    _name = 'l10n.bo.cancellation.reason'
    _description = 'Códigos de Motivos Anulación'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    
    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    def getCode(self):
        return self.codigoClasificador

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class OriginCountry(models.Model):
    _name = 'l10n.bo.origin.country'
    _description = 'Códigos de País'
    _order = 'codigoClasificador ASC'


    FORMAT={
        #ID_XML : SIAT_CODE
        'base.af':1,
        'base.al':2,
        'base.de':3,
        'base.ad':4,
        'base.ao':5,
        'base.ag':6,
        'base.sa':7,
        'base.dz':8,
        'base.ar':9,
        'base.am':10,
        'base.aw':199,
        'base.au':11,
        'base.at':12,
        'base.az':13,
        'base.bs':14,
        'base.bd':16,
        'base.bb':17,
        'base.bh':15,
        'base.bz':19,
        'base.bj':20,
        'base.bm':200,
        'base.by':18,
        'base.bo':22,
        'base.ba':23,
        'base.bw':24,
        'base.br':25,
        'base.bn':26,
        'base.bg':27,
        'base.bf':28,
        'base.bi':29,
        'base.bt':21,
        'base.be':30,
        'base.cv':31,
        'base.kh':32,
        'base.cm':33,
        'base.ca':34,
        'base.qa':142,
        'base.td':35,
        'base.cl':37,
        'base.cn':38,
        'base.cy':39,
        'base.co':40,
        'base.km':41,
        'base.cg':42,
        'base.kp':148,
        'base.kr':150,
        'base.cr':43,
        'base.ci':46,
        'base.hr':44,
        'base.cu':45,
        'base.dk':47,
        'base.dm':49,
        'base.ec':50,
        'base.eg':51,
        'base.sv':52,
        'base.ae':53,
        'base.er':54,
        'base.sk':55,
        'base.si':56,
        'base.es':57,
        'base.us':58,
        'base.ee':59,
        'base.et':60,
        'base.ru':61,
        'base.ph':63,
        'base.fi':64,
        'base.fj':62,
        'base.fr':65,
        'base.ga':66,
        'base.gm':67,
        'base.ge':68,
        'base.gh':69,
        'base.gd':70,
        'base.gr':71,
        'base.ml':112,
        'base.gl':202,
        'base.gt':72,
        'base.gn':73,
        'base.gq':74,
        'base.gw':75,
        'base.gy':76,
        'base.ht':77,
        'base.hn':78,
        'base.hk':206,
        'base.hu':79,
        'base.in':80,
        'base.id':81,
        'base.iq':82,
        'base.ie':83,
        'base.ir':84,
        'base.is':85,
        'base.ky':201,
        'base.ck':86,
        'base.fo':87,
        'base.fk':203,
        'base.mh':88,
        'base.sb':89,
        'base.vg':209,
        'base.il':90,
        'base.it':91,
        'base.jm':92,
        'base.jp':93,
        'base.jo':94,
        'base.la':145,
        'base.ls':100,
        'base.lv':101,
        'base.lr':102,
        'base.ly':103,
        'base.li':211,
        'base.lt':104,
        'base.lu':105,
        'base.mk':196,
        'base.mg':107,
        'base.my':108,
        'base.mw':109,
        'base.mv':110,
        'base.ml':112,
        'base.mt':111,
        'base.ma':113,
        'base.mu':114,
        'base.mr':115,
        'base.fm':116,
        'base.md':151,
        'base.mn':117,
        'base.me':118,
        'base.mz':119,
        'base.mx':121,
        'base.mc':122,
        'base.na':123,
        'base.nr':124,
        'base.np':125,
        'base.ni':126,
        'base.ng':127,
        'base.nu':128,
        'base.no':129,
        'base.nz':130,
        'base.ne':131,
        'base.om':132,
        'base.pk':133,
        'base.pw':134,
        'base.pa':135,
        'base.pg':136,
        'base.py':137,
        'base.nl':138,
        'base.pe':139,
        'base.pl':140,
        'base.pt':141,
        'base.pr':205,
        'base.uk':143,
        'base.cf':144,
        'base.cz':36,
        'base.cd':146,
        'base.do':147,
        'base.rw':154,
        'base.ro':153,
        'base.ws':156,
        'base.kn':155,
        'base.sm':157,
        'base.vc':158,
        'base.lc':159,
        'base.st':160,
        'base.sn':161,
        'base.rs':162,
        'base.sc':163,
        'base.sl':164,
        'base.sg':165,
        'base.sy':152,
        'base.so':166,
        'base.lk':167,
        'base.sz':174,
        'base.za':168,
        'base.sd':169,
        'base.ss':170,
        'base.se':171,
        'base.ch':172,
        'base.sr':173,
        'base.th':175,
        'base.tw':210,
        'base.tz':149,
        'base.tj':176,
        'base.tl':177,
        'base.tg':178,
        'base.tk':179,
        'base.to':180,
        'base.tt':181,
        'base.tm':182,
        'base.tr':183,
        'base.tv':184,
        'base.tn':185,
        'base.ua':186,
        'base.ug':187,
        'base.uy':188,
        'base.uz':189,
        'base.vu':190,
        'base.ve':191,
        'base.vn':192,
        'base.ye':193,
        'base.zm':194,
        'base.zw':195
        

        #anguila no la posee el siat
        #Antártida no la posee el siat
        #Birmania no la posee el siat
        #Bonaire, San Eustaquio y Saba no la posee el siat
        #Curazao no la posee el siat
        #Gibraltar no la posee el siat
        #Guadalupe no la posee el siat
        #Guam no la posee el siat
        #Guayana Francesa no la posee el siat
        #Guernsey no la posee el siat
        #Isla Bouvet no la posee el siat
        #Isla Norfolk no la posee el siat
        #Isla de Man no la posee el siat
        #Isla de Navidad no la posee el siat
        #Islas Cocos (Keeling) no la posee el siat
        #Islas Georgias del Sur y Sandwich del Sur no la posee el siat
        #Islas Marianas del Norte no las posee el siat
        #Islas Pitcairn no la posee el siat
        #Islas Turcas y Caicos no las posee el siat
        #Islas Ultramarinas Menores de los Estados Unidos no las posee el siat
        #Jersey no la posee el siat
        #Kosovo no la posee el siat
        #libano no la posee el siat
        #Macao no la posee el siat
        #Martinica no la posee el siat
        #Mayotte no la posee el siat
        #Montserrat no la posee el siat
        #Nueva Caledonia no la posee el siat
        #Palestina no la posee el siat
        #Polinesia Francesa no la posee el siaT
        #Reunión no la posee el siat
        #Sahara Occidental no la posee el siat
        #Samoa Americana no la posee el siat
        #San Bartolomé no la posee el siat
        #San Martín (parte francesa) no la psee el siat
        #San Martín (parte neerlandesa) no la posee el siat
        #San Pedro y Miquelón no la posee el siat
        #Santa Elena, Ascensión y Tristán de Acuña no la posee el siat
        #Santa Sede (Estado de la Ciudad del Vaticano) no la posee el siat
        #Svalbard y Jan Mayen no la posee el siat
        #Territorio británico del Océano Índico no la posee el siat
        #Territorio de las Islas Heard y McDonald no la posee el siat
        #Tierras Australes y Antárticas Francesas no la posee el siat
        #Wallis y Futuna no la posee el siat
        #Yibuti no la posee el siat
        #Åland no la posee el siat 
    }
    
    codigoClasificador = fields.Integer(
        string='Codigo', 
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion'
    )

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def getCode(self):
        return self.codigoClasificador
    
    def getName(self):
        return self.descripcion
    
    def _format(self):
        for metadata, code in self.FORMAT.items():
            odoo_record = self.env.ref(metadata, False)
            siat_record = self.search([('codigoClasificador','=',code)], limit=1)
            if odoo_record and siat_record:
                odoo_record.write({'l10n_bo_country_id' : siat_record.id})



class TypeDocumentIdentity(models.Model):
    _name = 'l10n.bo.type.document.identity'
    _description = 'Códigos de Tipo Documento Identidad'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    
    def complete_name(self):
        for leg in self.search([]):
            leg._compute_name()

    def getCode(self):
        if self.codigoClasificador == 0:
            raise UserError('Error de codigo documento identidad')
        return self.codigoClasificador


    name = fields.Char(
        string='Name', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

xsd_names = {
    '1-1': 'facturaElectronicaCompraVenta.xsd',
    '1-24': ''
}


class L10nLatamDocumentType(models.Model):
    _name = 'l10n.bo.document.type'
    _description = 'Codigos de tipo documento'
    _order = 'codigoClasificador ASC'
    
    name = fields.Char(
        string='Nombre',
        store=True,
        compute='_compute_name'
    )

    codigoClasificador = fields.Integer(
        string='Código',
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    
    
    cafc_ids = fields.One2many(
        string="CAFC's",
        comodel_name='l10n.bo.cafc',
        inverse_name='document_type_id',
    )
    
    

    use = fields.Boolean(
        string='Activo',
        company_dependent=True,
    )

    def getServiceType(self):
        return self.sector_document_id.getServiceType()
    
    def getModalityType(self):
        return self.sector_document_id.getModalityType()
    
    def getReceptionMethod(self):
        return self.invoice_type_id.getReceptionMethod()
    
    def getVerificationMethod(self):
        return self.invoice_type_id.getVerificationMethod()
    
    

    


    def getCode(self):
        return self.codigoClasificador
    
    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    
    invoice_type_id = fields.Many2one(
        string='Tipo factura',
        comodel_name='l10n.bo.type.invoice',
        copy=False
    )

    
    sector_document_id = fields.Many2one(
        string='Documento sector',
        comodel_name='l10n.bo.activity.document.sector',
        company_dependent=True,
    )
    



    def _format(self):
        # INVOICE TYPE
        with_tax_credit_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',1)], limit=1)
        document_type_with_tax_credit_ids = self.search(
            [
                ('codigoClasificador','in',[1,2,11,12,13,14,15,16,17,18,19,21,22,23,31,34,35,37,38,39,41,44,51,53])
            ]
        )
        if with_tax_credit_id and document_type_with_tax_credit_ids:
            for document_id in document_type_with_tax_credit_ids:
                document_id.write({'invoice_type_id':with_tax_credit_id.id})
        
        without_tax_credit_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',2)], limit=1)
        document_type_without_tax_credit_ids = self.search(
            [
                ('codigoClasificador','in',[3,4,5,6,7,8,9,10,20,28,33,36,40,42,43,45,46,49,50,52])
            ]
        )
        if without_tax_credit_id and document_type_without_tax_credit_ids:
            for document_id in document_type_without_tax_credit_ids:
                document_id.write({'invoice_type_id':without_tax_credit_id.id})
        
        adjustment_document_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',3)], limit=1)
        document_type_adjustment_document_ids = self.search(
            [
                ('codigoClasificador','in',[24,29,47,48])
            ]
        )
        if adjustment_document_id and document_type_adjustment_document_ids:
            for document_id in document_type_adjustment_document_ids:
                document_id.write({'invoice_type_id':adjustment_document_id.id})


        equivalent_document_id = self.env['l10n.bo.type.invoice'].search([('codigoClasificador','=',4)], limit=1)
        document_type_equivalent_document_ids = self.search(
            [
                ('codigoClasificador','in',[30])
            ]
        )
        if equivalent_document_id and document_type_equivalent_document_ids:
            for document_id in document_type_equivalent_document_ids:
                document_id.write({'invoice_type_id':equivalent_document_id.id})


        # SET SECTOR DOCUMENTS
        sector_document_ids = self.env['l10n.bo.activity.document.sector'].search([])
        for sector_document_id in sector_document_ids:
            document_type_id = self.search([('codigoClasificador','=',sector_document_id.getCode())], limit=1)
            if document_type_id:
                document_type_id.write({'sector_document_id' : sector_document_id.id, 'use' : True})

class TypeEmision(models.Model):
    _name = 'l10n.bo.type.emision'
    _description = 'Códigos de Tipo Emisión'
    _order = 'codigoClasificador ASC'
    
    codigoClasificador = fields.Integer(
        string='Codigo', 
        readonly=True 
    )
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )
    legend = fields.Text(
        string='Leyenda'
    )
    
    

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    def _format(self):
        emision_online = self.search([('codigoClasificador','=',1)], limit=1)
        if emision_online:
            emision_online.write({'legend': """“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido en una modalidad de facturación en línea”."""})
            
            pos_ids = self.env['l10n.bo.pos'].search([('company_id','=',self.env.company.id)])
            _logger.info('Obteniendo la lista de puntos de venta')
            for pos_id in pos_ids:
                _logger.info('Recoriendo la lista de puntos de venta')
                if not pos_id.emision_id:
                    pos_id.action_online(True)


        emision_offline = self.search([('codigoClasificador','=',2)], limit=1)
        if emision_offline:
            emision_offline.write({'legend': """“Este documento es la Representación Gráfica de un Documento Fiscal Digital emitido fuera de línea, verifique su envío con su proveedor o en la página web www.impuestos.gob.bo"."""})
            

class TypeRoom(models.Model):
    _name = 'l10n.bo.type.room'
    _description = 'Codigos tipo de habitación'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador
    
    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )


    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class TypePayment(models.Model):
    _name = 'l10n.bo.type.payment'
    _description = 'Códigos de Tipo Método Pago'
    _order = 'codigoClasificador ASC'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )



class TypeCurrency(models.Model):
    _name = 'l10n.bo.type.currency'
    _description = 'Códigos de Tipo Moneda'

    FORMAT ={
       #ID_XML : SIAT_CODE
        'base.BOB':1,
        'base.USD':2,
        'base.AED':95,
        'base.AFN':3,
        'base.ALL':4,
        'base.AMD':10,
        'base.ANG':41,
        'base.AOA':8,
        'base.ARS':9,
        'base.AUD':12,
        'base.AWG':11,
        'base.AZN':13,
        'base.BAM':21,
        'base.BBD':17,
        'base.BDT':16,
        'base.BGN':25,
        'base.BHD':15,
        'base.BIF':28,
        'base.BND':24,
        'base.BRL':23,
        'base.BSD':14,
        'base.BTN':20,
        'base.BWP':22,
        'base.BYN':18,
        'base.BYR':18,
        'base.BZD':19,
        'base.CAD':30,
        'base.CDF':37,
        'base.CHF':133,
        'base.CLP':33,
        'base.CNY':34,
        'base.COP':35,
        'base.CRC':38,
        'base.CUP':40,
        'base.CVE':31,
        'base.CZK':42,
        'base.DJF':44,
        'base.DKK':43,
        'base.DOP':45,
        'base.EGP':47,
        'base.ERN':49,
        'base.EUR':7,
        'base.GBP':5,
        'base.GEL':53,
        'base.GHS':54,
        'base.GIP':55,
        'base.GMD':52,
        'base.GNF':57,
        'base.GTQ':56,
        'base.HKD':154,
        'base.HNL':59,
        'base.HRK':39,
        'base.HTG':58,
        'base.HUF':60,
        'base.IDR':63,
        'base.ILS':66,
        'base.INR':62,
        'base.IQD':65,
        'base.IRR':64,
        'base.ISK':61,
        'base.JMD':67,
        'base.JOD':69,
        'base.JPY':68,
        'base.KES':71,
        'base.KGS':75,
        'base.KHR':29,
        'base.KMF':36,
        'base.KPW':72,
        'base.KRW':73,
        'base.KWD':74,
        'base.KYD':32,
        'base.KZT':70,
        'base.LAK':76,
        'base.LBP':78,
        'base.LRD':80,
        'base.LSL':79,
        'base.LTL':82,
        'base.LVL':77,
        'base.LYD':81,
        'base.MDL':93,
        'base.MGA':85,
        'base.MKD':84,
        'base.MNT':94,
        'base.MOP':83,
        'base.MRU':89,
        'base.MUR':90,
        'base.MXN':91,
        'base.MZN':96,
        'base.NAD':97,
        'base.NGN':102,
        'base.NIO':101,
        'base.NOK':103,
        'base.NPR':99,
        'base.NZD':100,
        'base.OMR':104,
        'base.PAB':106,
        'base.PEN':109,
        'base.PGK':107,
        'base.PHP':110,
        'base.PKR':105,
        'base.PLN':111,
        'base.PYG':108,
        'base.QAR':112,
        'base.RON':113,
        'base.RSD':120,
        'base.RUB':18,
        'base.RWF':115,
        'base.SAR':119,
        'base.SBD':124,
        'base.SCR':121,
        'base.SDG':129,
        'base.SEK':132,
        'base.SGD':123,
        'base.SLE':122,
        'base.SOS':125,
        'base.SRD':130,
        'base.SSP':127,
        'base.STD':118,
        'base.STN':118,
        'base.SVC':48,
        'base.SYP':134,
        'base.SZL':131,
        'base.TJS':136,
        'base.TMT':143,
        'base.TND':141,
        'base.TRY':142,
        'base.TTD':140,
        'base.TWD':135,
        'base.TZS':137,
        'base.UAH':145,
        'base.UGX':144,
        'base.UYU':146,
        'base.UZS':147,
        'base.VEF':149,
        'base.VND':150,
        'base.VUV':148,
        'base.XOF':26,
        'base.XCD':116,
        'base.XPF':51,
        'base.YER':151,
        'base.ZAR':126,
        'base.ZMW':152,
        'base.ZWL':153

        #Chinese yuan - Offshore no la posee el siat
        #Unidad de Valor Real no la posee el siat
        #Cuban convertible peso no la posee el siat
        #Algerian dinar no la posee el siat
        #Ethiopian birr no la posee el siat
        #Fiji dollar no la posee el siat
        #Falkland Islands pound  no la posee el siat
        #Dólar guyanés no la posee el siat
        #Sri Lankan rupee no la posee el siat
        #Moroccan dirham no la pòsee el siat
        #Myanmar kyat no la posee el siat
        #Mauritanian ouguiya (old) no la posee el siat
        #Maldivian rufiyaa no las posee el siat
        #Malawian kwacha no la posee el siat
        #Malaysian ringgit no la posee el siat 
        #Saint Helena pound no la posee el siat
        #Thai baht no la posee el siat
        #Tongan paʻanga no la posee el siat
        #Uruguay Peso en Unidades Indexadas no las posee el siat
        #Unidad previsional no la posee el siat
        #Venezuelan bolívar soberano el siat no la posee
        #Samoan tālā no la posee el siat
        #CFA franc BEAC no la posee el siat
        #Zimbabwe Gold no la posee el siat
    }


    codigoClasificador = fields.Integer(
        string='Codigo',    
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripcion',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador
    
    def getName(self):
        return self.descripcion

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def _format(self):
        for metadata, code in self.FORMAT.items():
            odoo_record = self.env.ref(metadata, False)
            siat_record = self.search([('codigoClasificador','=',code)], limit=1)
            if odoo_record and siat_record:
                odoo_record.write({'siat_currency_id' : siat_record.id})

        # base_bo, base_usd = self.env['res.currency'].search([('id','=',62)], limit=1), self.env['res.currency'].search([('id','=',1)], limit=1)
        # siat_bo, siat_usd = self.search([('codigoClasificador','=',1)], limit=1), self.search([('codigoClasificador','=',2)], limit=1)
        
        # if base_bo and siat_bo:
        #     base_bo.write(
        #         {
        #             'siat_currency_id' : siat_bo.id
        #         }
        #     )
        # if base_usd and siat_usd:
        #     base_usd.write(
        #         {
        #             'siat_currency_id' : siat_usd.id
        #         }
        #     )
        
        




class TypePos(models.Model):
    _name = 'l10n.bo.type.point.sale'
    _description = 'Códigos tipo de punto de venta'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )

    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )


class TypeInvoice(models.Model):
    _name = 'l10n.bo.type.invoice'
    _description = 'Códigos de Tipo Factura'

    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )     
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    def getCode(self):
        return self.codigoClasificador
    
    def getReceptionMethod(self):
        if self.codigoClasificador in [1,2]:
            return 'recepcionFactura'
        if self.codigoClasificador == 3:
            return 'recepcionDocumentoAjuste'
        
        if self.codigoClasificador == 4:
            raise UserError('La recepcion de documentos equivalentes no esta implementado')
        
    def getVerificationMethod(self):
        if self.codigoClasificador in [1,2]:
            return 'verificacionEstadoFactura'
        if self.codigoClasificador == 3:
            return 'verificacionEstadoDocumentoAjuste'
        
        if self.codigoClasificador == 4:
            raise UserError('La recepcion de documentos equivalentes no esta implementado')
        

    def getObjectName(self, method):
        if method == 'recepcionFactura':
            return 'SolicitudServicioRecepcionFactura'
        if method == 'recepcionDocumentoAjuste':
            return 'SolicitudServicioRecepcionDocumentoAjuste'
        
        if method == 'verificacionEstadoFactura':
            return 'SolicitudServicioVerificacionEstadoFactura'
        if method == 'verificacionEstadoDocumentoAjuste':
            return 'SolicitudServicioVerificacionEstadoDocumentoAjuste'
        
        raise UserError(f'No se encontro un nombre de objeto para el metodo: {method}')
        
        # if method == 'recepcionDocumentoAjuste':
        #     return 'SolicitudServicioRecepcionDocumentoAjuste'
        # if method == 'recepcionDocumentoAjuste':
        #     return 'SolicitudServicioRecepcionDocumentoAjuste'
        # if method == 'recepcionDocumentoAjuste':
        #     return 'SolicitudServicioRecepcionDocumentoAjuste'
        # if method == 'recepcionDocumentoAjuste':
        #     return 'SolicitudServicioRecepcionDocumentoAjuste'
        

        
        

    

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )
    
    def _format(self):
        pass



class TypeUnitMeasurement(models.Model):
    _name = 'l10n.bo.type.unit.measurement'
    _description = 'Códigos de Unidad de Medida'

    FORMAT = { 
        #UNIDADES DE MEDIDAS
        #ID_XML : SIAT_CODE

        'uom.product_uom_unit':58,
        'uom.product_uom_dozen':14,
        'uom.product_uom_gram':17,
        'uom.product_uom_oz':40,
        'uom.product_uom_lb':27,
        'uom.product_uom_kgm':22,
        'uom.product_uom_ton':55,
        'uom.product_uom_hour':71,
        'uom.product_uom_day':67,
        'uom.product_uom_millimeter':35,
        'uom.product_uom_cm':10,
        'uom.product_uom_inch':50,
        'uom.product_uom_foot':44,
        'uom.product_uom_yard':60,
        'uom.product_uom_meter':30,
        'uom.product_uom_km':23,
        'uom.product_uom_mile':38,
        'uom.uom_square_foot':45,
        'uom.uom_square_meter':31,
        'uom.product_uom_cubic_inch':62,
        'uom.product_uom_floz':62,
        'uom.product_uom_qt': 88,
        'uom.product_uom_litre':28,
        'uom.product_uom_gal':59,
        'uom.product_uom_cubic_foot':46,
        'uom.product_uom_cubic_meter':89
    }
    
    codigoClasificador = fields.Integer(
        string='Codigo',
        readonly=True 
    )
    descripcion = fields.Text(
        string='Descripción',
        readonly=True 
    )

    name = fields.Char(
        string='Nombre', 
        store=True, 
        compute='_compute_name'
    )

    @api.depends('codigoClasificador', 'descripcion')
    def _compute_name(self):
        for leg in self:
            leg.name = '%s - %s' % (leg.codigoClasificador or '', leg.descripcion or '')
    
    def getCode(self):
        return self.codigoClasificador
    
    def getDescription(self):
        return self.descripcion

    def create_records(self, res, company_id = None):
        for activity in res.listaCodigos:
            record_exist = self.search([('codigoClasificador','=',activity.codigoClasificador)], limit=1)
            if record_exist:
                record_exist.write({'descripcion' : activity.descripcion})
            else:
                self.create(
                    {
                        'codigoClasificador': activity.codigoClasificador,
                        'descripcion': activity.descripcion,
                    }
                )

    def _format(self):
        for metadata, code in self.FORMAT.items():
            odoo_record = self.env.ref(metadata, False)
            siat_record = self.search([('codigoClasificador','=',code)], limit=1)
            if odoo_record and siat_record:
                odoo_record.write({'siat_udm_id' : siat_record.id})

        # siat_unit, siat_dozen = self.search([('codigoClasificador','=',58)], limit=1), self.search([('codigoClasificador','=',14)], limit=1)
        # uom_unit, uom_dozen = self.env['uom.uom'].search([('id','=',1)], limit=1), self.env['uom.uom'].search([('id','=',2)], limit=1)

        # if uom_unit and siat_unit:
        #     uom_unit.write(
        #         {
        #             'siat_udm_id' : siat_unit.id
        #         }
        #     )

        # if uom_dozen and siat_dozen:
        #     uom_dozen.write(
        #         {
        #             'siat_udm_id' : siat_dozen.id
        #         }
        #     )