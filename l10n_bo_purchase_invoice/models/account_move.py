# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import os
import base64
from odoo.exceptions import ValidationError
from lxml import objectify
from lxml import etree

import pytz
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    # FIELDS
    bo_purchase_edi = fields.Boolean(
        string='Factura compra (BO)',
        related='journal_id.bo_purchase_edi',
        readonly=True,
        store=True
    )

    
    # invoice_date_purchase_edi = fields.Datetime(
    #     string='Fecha hora',
    #     default=fields.Datetime.now,
    #     help='Fecha hora factura compra'        
    # )
    
    
    # bo_purchase_edi_validated = fields.Boolean(
    #     string='Factura compra validada',
    #     copy=False
    # )

    purchase_type = fields.Selection(
        string='Tipo compra',
        selection=[
            ('1', '(1) Compras para mercado interno con destino a actividades gravadas.'), 
            ('2', '(2) Compras para mercado interno con destino a actividades no gravadas.'),
            ('3', '(3) Compras sujetas a proporcionalidad.'),
            ('4', '(4) Compras para exportaciones.'),
            ('5', '(5) Compras tanto para el mercado interno como para exportaciones')
        ],
        default='1',
        required=True
    )

    edi_purchase_str = fields.Text(
        string='Formato compra EDI',
        copy=False,
        readonly=True
    )

    dui_dim_number = fields.Char(
        string='Numero DUI/DIM',
        copy=False,
        default='0'
    )

    
    purchase_control_code = fields.Char(
        string='Codigo control',
        copy=False,
        default='0'
    )

    invoice_number = fields.Float(
        string='Nro. Factura',
        copy=False, 
        digits=(20, 0)
    )

    purchase_number = fields.Float(
        string='Nro. Compra',
        copy=False, 
        digits=(20, 0),
        default=0
    )

    

    cuf = fields.Char(
        string='CUF',
        help='Codigo unico de facturación.',
        copy=False,
    )

    
    origin_invoice_type = fields.Selection(
        string='Tipo origen',
        selection=[('national', 'Factura/Nota fiscal'), ('international', 'Importaciones - DUI/DIM'), ('ticket', 'Boleto Aéreo')],
        default= lambda self : self.get_default_origin_invoice_type()
    )

    def get_default_origin_invoice_type(self):
        move_type = self.env.context.get('default_move_type')
        if move_type == 'in_invoice':
            return 'national'
        return ''
    

    
    is_dui_dim = fields.Boolean(
        string='¿Es compra con DUI DIM?',
        compute='_compute_is_dui_dim' 
    )
    
    def _compute_is_dui_dim(self):
        for record in self:
            #tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_dui_dim_purchase_group', False)
            record.is_dui_dim = round(self.get_purchase_group_amount('dui_dim'), 2) > 0 #record.get_purchase_group_amount(tax_group.name, tax_group.id) > 0 if tax_group else False
    
    
    
    
    
    reazon_social = fields.Char(
        string='Razón social',
        copy=False
    )

    nit_ci = fields.Char(
        string='NIT/CI',
        copy=False
    )
    
    @api.onchange('partner_id')
    def _onchange_partner_supplier(self):
        if self.partner_id and not self.nit_ci:
            self.nit_ci = self.partner_id.vat
        
        if self.partner_id and not self.reazon_social:
            self.reazon_social = self.partner_id.name
        
    
    @api.constrains('partner_id')
    def _check_partner_supplier(self):
        for record in self:
            if record.partner_id:
                if not record.nit_ci:
                    self.write({'nit_ci' : self.partner_id.vat})
            
                if not record.reazon_social:
                    self.write({'reazon_social' : self.partner_id.name})
            
    
    
    
    

    def next_purchase_sequence(self):
        for record in self:
            if record.bo_purchase_edi:
                record.journal_id.next_purchase_sequence()
    
    def generate_purchase_sequence(self):
        self.write({'purchase_number' : self.journal_id.get_purchase_sequence()})
    
    def get_purchase_sequence(self):
        for record in self:
            if record.bo_purchase_edi:
                if record.purchase_number==0:
                    record.generate_purchase_sequence()
                    record.next_purchase_sequence()
                return int(record.purchase_number)
            return 0
    
    def getAmountImport(self):
        tax_group = 'dui_dim'
        return round(self.get_purchase_group_amount(tax_group), 2)
        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_dui_dim_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    
    def getAmountTotalSupplier(self) -> float :
        amount_total = self.getAmountImport()
        if amount_total <= 0:
            amount_total = 0
            for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.global_discount:
                    amount_total += line.quantity * line.price_unit
        return round(amount_total + self.getAmountDisccountSupplier(), 2)
    
    def getAmountSubTotalSupplier(self):
        amount = self.getAmountTotalSupplier() - self.getAmountIceFromSupplier() - self.getAmountIehdFromSupplier() - self.getAmountIpjFromSupplier() - self.getAmountRateFromSupplier() - self.getAmountNoIvaFromSupplier() - self.getAmountExemptFromSupplier() - self.getAmountZeroRateFromSupplier()
        return round(amount, 2)

    def getAmountDisccountSupplier(self):
        discount_void = getattr(self, 'getAmountDiscount', False)
        discount_line_void = getattr(self, 'getAmountLineDiscount', False)

        return round( discount_void() if discount_void else 0 + discount_line_void() if discount_line_void else 0 , 2)
    
    def getAmountGifCardSuppllier(self):
        gift_card_void = getattr(self,'getAmountGiftCard', False)
        return gift_card_void() if gift_card_void else 0
    
    def getControlCodeSupplier(self):
        return self.purchase_control_code if self.purchase_control_code else '0'
    # -- TAXS --
    
    def check_tax_group(self, column_rc_type):
        for invoice_line_id in self.invoice_line_ids:
            if invoice_line_id.group_in_taxs(column_rc_type):
                return True
        return False
    
    def get_purchase_group_amount(self, column_rc_type):
        amount = 0
        _logger.info('METODO DE RASTREO DE GRUPOS')
        if self.check_tax_group(column_rc_type):
            _logger.info(f'BUSCANDO GRUPO: {column_rc_type}')
            finded_group = False
            if self.tax_totals:
                groups = self.tax_totals.get('groups_by_subtotal', [])
                if groups:
                    base_list = groups.get('Subtotal', [])
                    if base_list:
                        for base in base_list:
                            base_name, base_id = base.get('tax_group_name', ''), base.get('tax_group_id', 0)
                            tax_group_id = self.env['account.tax.group'].browse(base_id)
                            if tax_group_id and tax_group_id.column_rc_type == column_rc_type:
                                finded_group = True
                                base_amount = base.get('tax_group_amount', False)
                                if base_amount:
                                    amount = base_amount
                                    break
            if not finded_group:
                raise UserError(f'Error de calculo: {column_rc_type}, no encontrado')
        return amount
    
    '''
    defaultdict(
        <class 'list'>, {
            'Subtotal': [
                {
                    'group_key': 23, 
                    'tax_group_id': 23, 
                    'tax_group_name': 'RC Tasa cero', 
                    'tax_group_amount': 100.0, 
                    'tax_group_base_amount': 100.0, 
                    'formatted_tax_group_amount': '100,00\xa0Bs.', 
                    'formatted_tax_group_base_amount': '100,00\xa0Bs.', 
                    'hide_base_amount': False
                }
            ]
        }
    )'''
    
    def getAmountIceFromSupplier(self):
        tax_group = 'ice'
        return round(self.get_purchase_group_amount(tax_group), 2)
    
    def getAmountIehdFromSupplier(self):
        tax_group = 'iehd'
        return round(self.get_purchase_group_amount(tax_group), 2)
        #tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_iehd_purchase_group', False)
        #return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountIpjFromSupplier(self):
        tax_group = 'ipj'
        return round(self.get_purchase_group_amount(tax_group), 2)
        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_ipj_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountRateFromSupplier(self):
        tax_group = 'rate'
        return round(self.get_purchase_group_amount(tax_group), 2)

        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_rate_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountNoIvaFromSupplier(self):
        tax_group = 'no_iva'
        return round(self.get_purchase_group_amount(tax_group), 2)
        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_no_iva_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountExemptFromSupplier(self):
        tax_group = 'exempt'
        return round(self.get_purchase_group_amount(tax_group), 2)
        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_exempt_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountZeroRateFromSupplier(self):
        tax_group = 'cero_rate'
        return round(self.get_purchase_group_amount(tax_group), 2)
        # tax_group = self.env.ref('l10n_bo_purchase_invoice.tax_zero_rate_purchase_group', False)
        # return round(self.get_purchase_group_amount(tax_group.name, tax_group.id), 2) if tax_group else 0
    
    def getAmountOnIvaSupplier(self):
        amount = self.getAmountSubTotalSupplier() - self.getAmountDisccountSupplier() - self.getAmountGifCardSuppllier()
        return round(amount, 2)
    
    def getEmisorNIT(self):
        if self.nit_ci or self.partner_id:
            nit = self.nit_ci or self.partner_id.vat
            if nit:
                return nit
        raise UserError(f'Factura: {self.name}, ID: {self.id}, No se encontro un NIT/CI de proveedor')
    
    
    # @api.onchange('dui_dim_number')
    # def _onchange_dui_dim_number(self):
    #     if self.move_type == 'in_invoice':
    #         if self.dui_dim_number not in [False, '', '0'] and self.invoice_number != 0:
    #             self.invoice_number = 0
        
    
    # @api.constrains('dui_dim_number')
    # def _check_dui_dim_number(self):
    #     for record in self:
    #         if record.move_type == 'in_invoice':
    #             if record.dui_dim_number not in [False, '', '0'] and record.invoice_number != 0:
    #                 record.write({'invoice_number' : 0})
                
    
    @api.onchange('origin_invoice_type')
    def _onchange_origin_invoice_type(self):
        if self.move_type == 'in_invoice':
            if self.origin_invoice_type == 'national': #and (not record.dui_dim_number or record.dui_dim_number != '0'):
                self.dui_dim_number='0'
            elif self.origin_invoice_type == 'international':
                self.invoice_number= 0
                self.cuf='3'
            elif self.origin_invoice_type == 'ticket':
                self.cuf = '1'
                self.dui_dim_number = '0'

    
    @api.constrains('origin_invoice_type')
    def _check_origin_invoice_type(self):
        for record in self:
            if record.move_type == 'in_invoice':
                if record.origin_invoice_type == 'national' and (not record.dui_dim_number or record.dui_dim_number != '0'):
                    record.write({'dui_dim_number' : '0'})
                elif record.origin_invoice_type == 'international':
                    record.write({'invoice_number' : 0, 'cuf' : '3'})
                elif record.origin_invoice_type == 'ticket':
                    record.write({'cuf' : '1', 'dui_dim_number' : '0'})

    @api.constrains('origin_invoice_type')
    def _check_origin_invoice_type(self):
        for record in self:
            if record.move_type == 'in_invoice':
                if record.origin_invoice_type == 'national' and (not record.dui_dim_number or record.dui_dim_number != '0'):
                    record.write({'dui_dim_number' : '0'})
                elif record.origin_invoice_type == 'international':
                    record.write({'invoice_number' : 0, 'cuf' : '3'})
                elif record.origin_invoice_type == 'ticket':
                    record.write({'cuf' : '1', 'dui_dim_number' : '0'})


    
    def getInvoiceBillNumber(self):
        if self.origin_invoice_type in ['national', 'ticket']:
            if self.invoice_number > 0:
                return int(self.invoice_number)
            raise UserError(f'Factura: {self.name}, ID: {self.id}, El Nro. Factura debe ser mayor a cero 0')
        elif self.origin_invoice_type == 'international':
            if self.invoice_number == 0:
                return 0
            raise UserError(f'Factura: {self.name}, ID: {self.id}, El Nro. Factura debe ser igual a 0')
            
    def getRazonSocialSupplier(self, to_xml = False):
        nombreRazonSocial : str = self.reazon_social or self.partner_id.name
        if to_xml:
            # ESCAPAR
            nombreRazonSocial = nombreRazonSocial.replace('&','&amp;')
        return nombreRazonSocial
    
    def getDUIDIMNumber(self):
        if self.origin_invoice_type == 'international':
            if self.dui_dim_number not in [False, '0']:
                return self.dui_dim_number
            raise UserError(f'Factura: {self.name}, ID: {self.id}, El Nro. DUI DIM Debe ser establecido o diferente de cero 0')
        elif self.origin_invoice_type == 'national':
            if not self.dui_dim_number or self.dui_dim_number != '0':
                raise UserError(f'Factura: {self.name}, ID: {self.id}, El Nro. DUI DIM Debe ser igual a 0')
            return self.dui_dim_number
    
    # def write(self, values):
    #     """
    #         Update all record(s) in recordset, with new value comes as {values}
    #         return True on success, False otherwise
    
    #         @param values: dict of new values to be set
    
    #         @return: True on success, False otherwise
    #     """
    #     _logger.info(f"{values}")
    #     result = super(AccountMove, self).write(values)
    #     return result
    
    def getPurchaseType(self):
        if self.bo_purchase_edi:
            if self.purchase_type:
                _logger.info(self.purchase_type)
                return self.purchase_type
            raise UserError('No tiene un tipo de compra establecido.')
        
    
    def getCufSupplier(self):
        if self.origin_invoice_type == 'national':
            if self.cuf:
                return self.cuf
            raise UserError(f'Factura: {self.name}, ID: {self.id}, No se encontro un NIT/CI de proveedor')
        elif self.origin_invoice_type == 'international':
            if self.cuf != '3':
                raise UserError(f'Factura: {self.name}, ID: {self.id}, El CUF/Codigo de autorizacion debe ser igual a 3')
            return self.cuf
        elif self.origin_invoice_type == 'ticket':
            if self.cuf != '1':
                raise UserError(f'Factura: {self.name}, ID: {self.id}, El CUF/Codigo de autorizacion debe ser igual a 1')
            return self.cuf
    
    
    def action_purchase_edi(self):
        self.getInvoiceBillNumber()
        self.getDUIDIMNumber()
        self.getEmisorNIT()
        self.getPurchaseType()
        self.getCufSupplier()


    def _post(self,soft=True):
        res = super(AccountMove, self)._post(soft=soft)
        for record in res:
            if record.bo_purchase_edi:
                record.action_purchase_edi()
        return res