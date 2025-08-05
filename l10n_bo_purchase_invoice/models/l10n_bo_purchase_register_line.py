# -*- coding:utf-8 -*-

from odoo import api, models, fields

class L10nBoPurchaseRegisterLine(models.Model):
    _name = 'l10n.bo.purchase.register.line'
    _description = 'Linea de registro de compra (BO)'

    
    type = fields.Selection(
        string='Tipo linea',
        selection=[('invoice', 'Factura')],
        default='invoice',
    )
    
    
    invoice_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        readonly=True 
    )
    
    purchase_register_id = fields.Many2one(
        string='Registro de compra',
        comodel_name='l10n.bo.purchase.register',
    )
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company, 
        readonly=True
    )
    
    
    
    name = fields.Integer(
        string='N°',
        readonly=True 
    )

    
    specification = fields.Integer(
        string='ESPECIFICACIÓN',
        readonly=True 
    )
    
    
    nit = fields.Char(
        string='NIT PROVEEDOR',
        readonly=True 
    )

    
    reazon_social = fields.Char(
        string='RAZON SOCIAL PROVEEDOR',
        readonly=True 
    )
    
    autorization_code = fields.Char(
        string='CODIGO DE AUTORIZACION',
        readonly=True 
    )

    
    invoice_number = fields.Integer(
        string='NUMERO FACTURA',
        readonly=True 
    )
    
    
    dui_dim_number = fields.Char(
        string='NÚMERO DUI/DIM',
        readonly=True 
    )
    
    dui_dim_date = fields.Date(
        string='FECHA DE FACTURA/DUI/DIM',
    )
    
    
    amount_total = fields.Float(
        string='IMPORTE TOTAL COMPRA',
        readonly=True 
    )
    
    
    amount_ice = fields.Float(
        string='IMPORTE ICE',
        readonly=True 
    )
    
    
    amount_iehd = fields.Float(
        string='IMPORTE IEHD',
        readonly=True 
    )
    
    amount_ipj = fields.Float(
        string='IMPORTE IPJ',
    )
    
    
    amount_rate = fields.Float(
        string='TASAS',
        readonly=True 
    )
    
    
    amount_no_iva = fields.Float(
        string='OTRO NO SUJETO A CREDITO FISCAL',
        readonly=True 
    )
    
    
    amount_exempt = fields.Float(
        string='IMPORTES EXENTOS',
        readonly=True 
    )
    
    
    amount_cero_rate = fields.Float(
        string='IMPORTE COMPRAS GRAVADAS A TASA CERO',
        readonly=True 
    )
    
    
    amount_subtotal = fields.Float(
        string='SUBTOTAL',
        readonly=True 
    )
    
    amount_discount = fields.Float(
        string='DESCUENTOS/BONIFICACIONES /REBAJAS SUJETAS AL IVA',
        readonly=True 
    )
    
    
    amount_gift_card = fields.Float(
        string='IMPORTE GIFT CARD',
        readonly=True 
    )
    
    
    amount_base_fiscal_credit = fields.Float(
        string='IMPORTE BASE CF',
        readonly=True 
    )
    
    
    amount_fiscal_credit = fields.Float(
        string='CREDITO FISCAL',
        readonly=True 
    )
    
    purchase_type = fields.Char(
        string='TIPO COMPRA',
        readonly=True 
    )
    
    
    control_code = fields.Char(
        string='CÓDIGO DE CONTROL',
        readonly=True 
    )
    