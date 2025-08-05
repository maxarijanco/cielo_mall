# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import pytz
import io
import tarfile
import base64
import gzip
import hashlib

import logging
_logger = logging.getLogger(__name__)



class L10nBoSupplierPackage(models.Model):
    _name = "l10n.bo.supplier.package"
    _description = "Paquete proveedores (BO)"

    
    name = fields.Char(
        string='Nombre',
        readonly=True,
        default='Borrador'
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    
    
    state = fields.Selection(
        string='Estado',
        selection=[
            ('draft', 'Borrador'), 
            ('received', 'Recepcionado'),
            ('validated', 'Validado'),
            ('confirmed', 'Confirmado'),
            ('cancel', 'Cancelado')
        ],
        required=True,
        default='draft',
    )
    
    
    error = fields.Text(
        string='Error',
        copy=False
    )
    
    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        required=True,
        default= lambda self : self.get_branch_office_default()   
    )


    def get_branch_office_default(self):
        branch_office_id = self.env.company.branch_office_id
        return branch_office_id.id if branch_office_id else False 
    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
        required=True
    )

    
    @api.onchange('branch_office_id')
    def _onchange_branch_office_id(self):
        self.pos_id = self.branch_office_id.pos_id.id if self.branch_office_id and self.branch_office_id.pos_id else False 
    
    

    
    date_send = fields.Datetime(
        string='Fecha hora',
        default=fields.Datetime.now,
    )
    
    
    reception_code = fields.Char(
        string='Codigo recepción',
    )

    
    reception_state_code = fields.Integer(
        string='Codigo estado recepción',
    )
    

    
    reception_description = fields.Char(
        string='Estado recepcion',
    )
    
    
    supplier_package_line_ids = fields.One2many(
        string='Linea de paquete de proveedor',
        comodel_name='l10n.bo.supplier.package.line',
        inverse_name='supplier_package_id',
        required=True,
        ondelete='cascade'
    )
    supplier_message_line_ids = fields.One2many(
        string='Linea de mensaje de paquete de proveedor',
        comodel_name='l10n.bo.supplier.package.message',
        inverse_name='supplier_package_id',
    )

    
    success_reception = fields.Boolean(
        string='Recepcion coneccion',
        copy=False,
        readonly=True 
    )
     
    transaction_reception = fields.Boolean(
        string='Recepcion transaccion',
        copy=False,
        readonly=True 
    )

    
    multipacks = fields.Boolean(
        string='Gestionar paquetes',
        help='Habilita la opcion de enviar un paquete por factura de compra, en cada linea.',
        copy=False
    )
    

    
    gestion = fields.Integer(
        string='Gestion',
        default=fields.Datetime.now().year        
    )

    
    def get_gestion(self):
        if self.gestion>0:
            return self.gestion
        raise UserError('La gestion debe ser mayor a cero')

    
    period = fields.Integer(
        string='Periodo',
        default=fields.Datetime.now().month
    )

    def get_period(self):
        if self.period>0:
            return self.period
        raise UserError('El periodo debe ser mayor a cero')
    
    
    @api.model
    def create(self, values : dict):
        result = super(L10nBoSupplierPackage, self).create(values)
        for record in result:
            if record.name == 'Borrador':
                record.write(
                    {
                        'name' : record.env['ir.sequence'].next_by_code(record._name) or '/'
                    }
                )
        return result
    

    def get_invoices(self):
        invoice_ids : models.Model = self.env['account.move'].search(
            [
                ('move_type','=','in_invoice'),
                ('bo_purchase_edi','=',True),
                ('bo_purchase_edi_received','=',False),
                ('state','=','posted')
            ]
        )
        _logger.info(f"Facturas de proveeedores : {invoice_ids}")
        if invoice_ids:
            invoice_ids = invoice_ids.filtered(lambda invoice_id : invoice_id.invoice_date_edi.month == self.period and invoice_id.invoice_date_edi.year == self.gestion)
        if invoice_ids:        
            for invoice_id in invoice_ids:
                if invoice_id.id not in [ line.name.id for line in self.supplier_package_line_ids ]:
                    self.supplier_package_line_ids.create(
                        {
                            'name' : invoice_id.id,
                            'supplier_package_id' : self.id
                        }
                    )
    # #bo_purchase_edi_received
    
    def set_messages(self, mensajesList, move_id = None):
        #while self.supplier_message_line_ids:
        #    self.supplier_message_line_ids[0].unlink()

        for mensajes in mensajesList:
            self.supplier_message_line_ids.create(
                {
                    'name' : fields.datetime.now(),
                    'code' : mensajes.codigo,
                    'description' : mensajes.descripcion if not move_id else f"{move_id.name} : {mensajes.descripcion}",
                    'supplier_package_id' : self.id
                }
            )
    
    # # ----------------------------------------------------------------------------------------------------------

    def reception_action(self):
        if not self.multipacks:
            if not self.transaction_reception:
                if self.supplier_package_line_ids:
                    self.write({'date_send' : fields.datetime.now()})
                    RESPONSE = self.purchase_soap_service(METHOD='recepcionPaqueteCompras')
                    _logger.info(f"{RESPONSE}")
                    if RESPONSE:
                        if type(RESPONSE) == dict:
                            self.write({'success_reception' : RESPONSE.get('success', False)})
                            if self.success_reception:
                                DATA : dict = RESPONSE.get('data', False)
                                if DATA:
                                    self.write({'transaction_reception' : DATA.transaccion})
                                    if self.transaction_reception:
                                        self.write(
                                            {
                                                'state' : 'received',
                                                'reception_code' : DATA.codigoRecepcion,
                                                'reception_description' : DATA.codigoDescripcion,
                                                'reception_state_code' : DATA.codigoEstado
                                            }
                                        )

                                        for line in self.supplier_package_line_ids:
                                            line.name.write({'bo_purchase_edi_received' : True})
                                    if DATA.mensajesList:
                                        self.set_messages(DATA.mensajesList)
                            self.write({'error' : RESPONSE.get('error', False)})
                    else:
                        self.write({'error' : f"{RESPONSE}"})
            else:
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'MENSAJE',
                            'message': 'Los paquetes ya fueron recepcionados',
                            'sticky': False,
                        }
                }
    
    # def reception_actions(self):
    #     if self.multipacks:
    #         if self.supplier_package_line_ids:
    #             for line in self.supplier_package_line_ids:
    #                 line.reception_action()
    #             if all( line.transaction_reception for line in self.supplier_package_line_ids ):
    #                 self.write({'state' : 'received'})

    def purchase_soap_service(self, METHOD = None):
        PARAMS = [
                ('name','=',METHOD),
                ('environment_type','=', self.company_id.getL10nBoCodeEnvironment())
        ]
        WSDL_SERVICE = self.env['l10n.bo.operacion.service'].search(PARAMS,limit=1)
        #raise UserError(f"{PARAMS}")
        
        if WSDL_SERVICE:
            #raise UserError(WSDL_SERVICE.getWsdl())
            return getattr(self, f"{METHOD}", False)(WSDL_SERVICE)
        raise UserError(f'Servicio: {METHOD} no encontrado')

    # #####  < PARAMETROS DE EMISION > ####

    def getReceptionARGS(self, METHOD=False):
        if METHOD:
            gzip_buffer = io.BytesIO()
            with tarfile.open(fileobj=gzip_buffer, mode="w") as tar_file:
                for line in self.supplier_package_line_ids:
                    params_src = line.name.generate_edi_purchase_xml(_ir=True)
                    if params_src:
                        xml_content = params_src.datas
                        xml_content = base64.b64decode(xml_content)
                        _logger.info(f"XML: {xml_content}")
                        params_sio = io.BytesIO(xml_content)
                        info = tarfile.TarInfo(name=line.name.name + '.xml')
                        info.size = len(xml_content)
                        tar_file.addfile(tarinfo=info, fileobj=params_sio)
                    else:
                        raise UserError(f'No se encontró XML en factura: {line.name.name}')
            
            gzip_buffer.seek(0)
            #file_compress = gzip_buffer.getvalue()
            #_logger.info(f"Contenido comprimido: {file_compress}")
            
            if gzip_buffer:
                #_logger.info(f"VALUES: {self.supplier_package_line_ids[0].name.edi_purchase_format().encode('utf-8')}")
                file_compress = gzip.compress(gzip_buffer.getvalue())
                
                hash_string = hashlib.sha256(file_compress).hexdigest()
                return {
                    METHOD: {
                        'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
                        'codigoPuntoVenta': self.pos_id.getCode(),
                        'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                        'codigoSucursal': self.branch_office_id.getCode(),
                        'cufd': self.pos_id.getCufd(True),
                        'cuis': self.pos_id.getCuis(),
                        'nit': self.company_id.getNit(),
                        'archivo': file_compress,
                        'cantidadFacturas': len(self.supplier_package_line_ids),
                        'fechaEnvio': self.date_send.astimezone(pytz.timezone('America/La_Paz')).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
                        'gestion': self.get_gestion(),
                        'hashArchivo': hash_string,
                        'periodo': self.get_period()
                    }
                }
        
    #     raise UserError('NO se encontró un método para la operación')

    def recepcionPaqueteCompras(self, WSDL_SERVICE):
        OBJECT = self.getReceptionARGS(METHOD='SolicitudRecepcionCompras')
        _logger.info(f"PARAMETROS DE RECEPCION: {OBJECT}")
        
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.getDelegateToken()
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'recepcionPaqueteCompras')
        return WSDL_RESPONSE

    # ----------------------------------------------------------------------------------------------------------
    
    
    validation_success = fields.Boolean(
        string='Conección validacion',
        readonly=True 
    )
    
    validation_transaction = fields.Boolean(
        string='Valida',
        readonly=True 
    )

    
    validation_code = fields.Char(
        string='Codigo validacion',
    )
    
    validation_description = fields.Char(
        string='Estado validación',
    )

    
    validate_state_code = fields.Integer(
        string='Codigo estado validacion',
    )
    
    
    
    
    def validation_action(self):
        if not self.multipacks:
            if not self.validation_transaction:
                if self.supplier_package_line_ids:
                    RESPONSE = self.purchase_soap_service(METHOD='validacionRecepcionPaqueteCompras')
                    _logger.info(f"{RESPONSE}")
                    if RESPONSE:
                        if type(RESPONSE) == dict:
                            self.write({'validation_success' : RESPONSE.get('success', False)})
                            if self.validation_success:
                                DATA : dict = RESPONSE.get('data', False)
                                if DATA:
                                    self.write({'validation_transaction' : DATA.transaccion})
                                    if self.validation_transaction:
                                        self.write(
                                            {
                                                'state' : 'validated',
                                                'validation_code' : DATA.codigoRecepcion,
                                                'validation_description' : DATA.codigoDescripcion,
                                                'validate_state_code' : DATA.codigoEstado
                                            }
                                        )
                                    if DATA.mensajesList:
                                        self.set_messages(DATA.mensajesList)
                            self.write({'error' : RESPONSE.get('error', False)})
                    else:
                        self.write({'error' : f"{RESPONSE}"})
            else:
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'MENSAJE',
                            'message': 'Los paquetes ya fueron validados',
                            'sticky': False,
                        }
                }
            
    def getValidationARGS(self):
        return {
            'SolicitudValidacionRecepcionCompras' : {
                'codigoAmbiente' : self.company_id.getL10nBoCodeEnvironment(),
                'codigoPuntoVenta': self.pos_id.getCode(),
                'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                'codigoSucursal': self.branch_office_id.getCode(),
                'cufd': self.pos_id.getCufd(True),
                'cuis': self.pos_id.getCuis(),
                'nit': self.company_id.getNit(),
                'codigoRecepcion' : self.reception_code
            }
        }

    def validacionRecepcionPaqueteCompras(self, WSDL_SERVICE):
        OBJECT = self.getValidationARGS()
        _logger.info(f"PARAMETROS DE RECEPCION: {OBJECT}")
        
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.l10n_bo_delegate_token
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'validacionRecepcionPaqueteCompras')
        return WSDL_RESPONSE
    

    def confirm_action(self):
        RESPONSE = self.purchase_soap_service(METHOD='confirmacionCompras')
        _logger.info(f"{RESPONSE}")
        if RESPONSE:
                        if type(RESPONSE) == dict:
                            self.write({'validation_success' : RESPONSE.get('success', False)})
                            if self.validation_success:
                                DATA : dict = RESPONSE.get('data', False)
                                if DATA:
                                    self.write({'validation_transaction' : DATA.transaccion})
                                    if self.validation_transaction:
                                        self.write(
                                            {
                                                'state' : 'confirmed',
                                                'validation_code' : DATA.codigoRecepcion,
                                                'validation_description' : DATA.codigoDescripcion,
                                                'validate_state_code' : DATA.codigoEstado
                                            }
                                        )
                                    if DATA.mensajesList:
                                        self.set_messages(DATA.mensajesList)
                            self.write({'error' : RESPONSE.get('error', False)})
        else:
                        self.write({'error' : f"{RESPONSE}"})
        
    
    confirmation_date = fields.Datetime(
        string='Fecha confirmacion'
    )
    
    
    def getConfirmationARGS(self):
        if True:
            self.write({'confirmation_date' : fields.datetime.now()})
            gzip_buffer = io.BytesIO()
            with tarfile.open(fileobj=gzip_buffer, mode="w") as tar_file:
                for line in self.supplier_package_line_ids:
                    line.name.validate_confirmation_edi_purchase_xml()
                    params_src = line.name.generate_confirmation_edi_purchase_xml(_ir=True)
                    if params_src:
                        xml_content = params_src.datas
                        xml_content = base64.b64decode(xml_content)
                        _logger.info(f"XML: {xml_content}")
                        params_sio = io.BytesIO(xml_content)
                        info = tarfile.TarInfo(name=line.name.name + '.xml')
                        info.size = len(xml_content)
                        tar_file.addfile(tarinfo=info, fileobj=params_sio)
                    else:
                        raise UserError(f'No se encontró XML en factura: {line.name.name}')
            
            gzip_buffer.seek(0)
            #file_compress = gzip_buffer.getvalue()
            #_logger.info(f"Contenido comprimido: {file_compress}")
            
            if gzip_buffer:
                #_logger.info(f"VALUES: {self.supplier_package_line_ids[0].name.edi_purchase_format().encode('utf-8')}")
                file_compress = gzip.compress(gzip_buffer.getvalue())
                
                hash_string = hashlib.sha256(file_compress).hexdigest()
                return {
                    'SolicitudConfirmacionCompras': {
                        'codigoAmbiente': self.company_id.getL10nBoCodeEnvironment(),
                        'codigoPuntoVenta': self.pos_id.getCode(),
                        'codigoSistema': self.company_id.getL10nBoCodeSystem(),
                        'codigoSucursal': self.branch_office_id.getCode(),
                        'cufd': self.pos_id.getCufd(True),
                        'cuis': self.pos_id.getCuis(),
                        'nit': self.company_id.getNit(),
                        'archivo': file_compress,
                        'cantidadFacturas': len(self.supplier_package_line_ids),
                        'fechaEnvio': self.confirmation_date.astimezone(pytz.timezone('America/La_Paz')).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
                        'gestion': self.get_gestion(),
                        'hashArchivo': hash_string,
                        'periodo': self.get_period()
                    }
                }

    def confirmacionCompras(self, WSDL_SERVICE):
        OBJECT = self.getConfirmationARGS()
        _logger.info(f"PARAMETROS DE RECEPCION: {OBJECT}")
        
        WSDL = WSDL_SERVICE.getWsdl()
        TOKEN = self.company_id.l10n_bo_delegate_token
        WSDL_RESPONSE = WSDL_SERVICE.process_soap_siat(WSDL, TOKEN, OBJECT, 'confirmacionCompras')
        return WSDL_RESPONSE