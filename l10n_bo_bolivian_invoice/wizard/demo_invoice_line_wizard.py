# -*- coding:utf-8 -*- 
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)



class DemoInvoiceLineWizard(models.TransientModel):
    _name = "demo.invoice.line.wizard"
    _description = "Generador lineas de facturas para pruebas (BO)"

    
    
    
    pos_id = fields.Many2one(
        string='Punto de venta (BO)',
        comodel_name='l10n.bo.pos',
        related='demo_invoice_id.name',
        readonly=True,
        store=True
    )

    demo_invoice_id = fields.Many2one(
        string='Demo facturas',
        comodel_name='demo.invoice.wizard',
    )    
    
    document_type = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.document.type',
        required=True,
        domain=[('use','=',True)]
        
    )
        
    quantity = fields.Integer(
        string='Cantidad',
        default=1
    )

    product_id = fields.Many2one(
        string='Producto',
        comodel_name='product.product',
        required=True
    )

    
    confirm = fields.Boolean(
        string='Publicar automatico',
    )
    
    
    @api.model
    def create(self, values):
        demo_invoice_id = super(DemoInvoiceLineWizard, self).create(values)
        #demo_invoice_id.create_demo_invoices()

        if demo_invoice_id.document_type.getCode() == 1:
            pass
        return demo_invoice_id
    
    def get_document_type_id(self):
        if self.document_type:
            sequence_id = self.env['l10n.bo.pos.sequence'].search([('name','=',self.document_type.id),('pos_id','=',self.pos_id.id)], limit=1 )
            if sequence_id:
                return sequence_id.id
            raise UserError(f'{self.pos_id.name}, no tiene {self.document_type.name}')
        raise UserError('Debe asignar un tipo de documento')
    
    def getGeneralParams(self, date_time_now = False):
        return {
            'move_type' : 'out_invoice',
            'name' : '/',
            'partner_id' : self.demo_invoice_id.partner_id.id,
            'branch_office_id': self.pos_id.branch_office_id.id,
            'pos_id' : self.pos_id.id,
            'document_type_id' : self.get_document_type_id(),
            'journal_id' : self.demo_invoice_id.journal_id.id,
            'force_send' : True,
            'invoice_date_edi' : date_time_now if date_time_now else fields.datetime.now()
        }
    
    def getIncoterm(self):
        incoterm = self.env['account.incoterms'].search([], limit=1)
        if not incoterm:
            raise UserError('No se encontroraron incoterms')
        return incoterm.id
    
    def getCountry(self):
        country = self.env.ref('base.bo', False)
        if not country:
            raise UserError('No se encontro un pais')
        return country
    
    def getCountryState(self):
        country = self.getCountry()
        country_state = country.state_ids[0] if country.state_ids else False
        if not country_state:
            raise UserError('No se encontro un departamento')
        return country_state.id
    
    def getDefaultContact(self):
        res_parter = self.env['res.partner'].search([('supplier_rank','=',0)], limit=1)
        if not res_parter:
            raise UserError('No se encontro un contacto tipo cliente, por favor cree uno.')
        return res_parter

    def docParams(self, ARGS, to_continue):
            
            if self.document_type.getCode() in [1,8,13,14]:
                to_continue = True
            
            elif self.document_type.getCode() == 2:
                today_now = fields.datetime.now()
                ARGS['from_period'] = today_now.replace(day=1)
                ARGS['to_period'] = today_now
                to_continue = True

            elif self.document_type.getCode() == 3:
                ARGS['invoice_incoterm_id'] = self.getIncoterm()
                ARGS['country_id'] = self.getCountry().id
                ARGS['country_state_id'] = self.getCountryState()
                ARGS['destination_address'] = 'Calle laguna'
                to_continue = True
            
            elif self.document_type.getCode() == 4:
                ARGS['country_id'] = self.getCountry().id
                ARGS['country_state_id'] = self.getCountryState()
                to_continue = True
            
            elif self.document_type.getCode() == 11:
                today_now = fields.datetime.now()
                ARGS['from_period'] = today_now.replace(day=1)
                ARGS['to_period'] = today_now
                ARGS['contact_id'] = self.getDefaultContact().id
                to_continue = True
            
            elif self.document_type.getCode() == 28:
                ARGS['country_id'] = self.getCountry().id
                ARGS['destination_address'] = 'Portachuelo'
                to_continue = True
            return ARGS, to_continue

    def create_demo_invoices(self, date_time_now = False):
        if self.quantity>0:
            ARGS = False
            to_continue = False
            
            if self.document_type.getCode() not in [24, 47]:
                ARGS = self.getGeneralParams(date_time_now)
            else:
                ARGS = [
                    ('partner_id','=', self.demo_invoice_id.partner_id.id),
                    ('move_type','=','out_invoice'),
                    ('branch_office_id','=', self.pos_id.branch_office_id.id),
                    ('pos_id','=', self.pos_id.id),
                    ('document_type_id.codigoClasificador','in', [1,2,11]),
                    ('journal_id','=', self.demo_invoice_id.journal_id.id),
                    ('reversion','=',False),
                    ('state','=','posted'),
                    ('edi_state','in',['VALIDADA','REVERSION DE ANULACION CONFIRMADA']),
                ]
                to_continue = True
            
            ARGS, to_continue = self.docParams(ARGS, to_continue)
                
            
            if to_continue and ARGS:
                if self.document_type.getCode() not in [24, 47]:
                    PARAMS = [ARGS]
                    _logger.info('Creando facturas')
                    invoice_ids = self.env['account.move'].create(PARAMS*self.quantity)
                    if invoice_ids:
                        invoice_ids.write({'email_send' : False})
                        _logger.info('Creando lineas de facturas')
                        self.generate_line_ids(invoice_ids)
                        _logger.info('Publicando Facturas')
                        invoice_ids._post(soft = True)
                        #if self.confirm:
                        #    for invoice_id in invoice_ids:
                        #        invoice_id._post(soft = True)
                else:
                    invoice_ids = self.env['account.move'].search(ARGS, limit=self.quantity)
                    if invoice_ids:
                        _IDS = []
                        account_reversion_id = self.env['account.move.reversal'].create(
                            {
                                'date_mode' : 'custom',
                                'journal_id' : self.demo_invoice_id.journal_id.id,
                                'date' : fields.datetime.now(),
                                'move_ids': [(6,0,invoice_ids.ids)]
                            }
                        )
                        #raise UserError(account_reversion_id)
                        if account_reversion_id:
                            #raise UserError('Reversion creada')
                            account_reversion_id.reverse_moves()
            else:
                raise UserError(f"Hay tiene una implementacion para el documento: {self.document_type.name}")
        else:
            raise UserError('Debe generar cantidades mayores a 0')
    
    def generate_line_ids(self, invoice_ids):
        for invoice_id in invoice_ids:
            ARGS = {
                'product_id' : self.product_id.id,
                'name' : self.product_id.display_name,
                'move_id' : invoice_id.id,
            }
            if self.document_type.getCode() in [3,4]:
                if not self.product_id.siat_service_nandina_id:
                    raise UserError(f"No se encontro un codigo nandina para el producto: {self.product_id.name}")
                

            self.env['account.move.line'].create(
                ARGS
            )
