# -*- coding: utf-8 -*-

from odoo import api, models, fields
import html

from xml.sax.saxutils import escape

class AccountMove(models.Model):
    _inherit = ['account.move']
    
    # ------------------------------------------------------------------------------

    invoice_number = fields.Float(
        string='Nro. Factura',
        copy=False, 
        digits=(20, 0)
    )

    # ------------------------------------------------------------------------------
    
    edi_bo_invoice = fields.Boolean(
        string='Factura (BO)',
        #related='journal_id.bo_edi',
        readonly=False,
    )

    # ------------------------------------------------------------------------------

    invoice_date_edi = fields.Datetime(
        string='Fecha y hora (BO)',
        #default=fields.Datetime.now,
        copy=False
    )
    
    @api.constrains('invoice_date_edi','edi_bo_invoice')
    def _check_invoice_date_edi(self):
        for record in self:
            if record.edi_bo_invoice:
                record.invoice_date = record.invoice_date_edi
    

    # ------------------------------------------------------------------------------
    
    cuf = fields.Char(
        string='CUF',
        help='Codigo unico de facturación.',
        copy=False,
    )

    # ------------------------------------------------------------------------------
    
    edi_str = fields.Text(
        string='Formato edi',
        copy=False,
        readonly=True 
    )

    url = fields.Char(
        string='url',
        copy=False,
        readonly=False
    )

    # ------------------------------------------------------------------------------
    reazon_social = fields.Char(
        string='Razón social',
        copy=False
    )

    # ------------------------------------------------------------------------------
    nit_ci = fields.Char(
        string='NIT/CI',
        copy=False
    )
    
    # ------------------------------------------------------------------------------
    
    complement = fields.Char(
        string='Complemento',
        copy=False
    )
    # ------------------------------------------------------------------------------
    
    
    @api.constrains('partner_id')
    def _check_l10n_bo_partner_id(self):
        for record in self:
            reazon_social, nit_ci, complement = False, False, False
            if record.partner_id:
                reazon_social = record.partner_id.getNameReazonSocial()
                nit_ci = record.partner_id.getNit()
                complement = record.partner_id.getComplement()
            
            record.reazon_social =  reazon_social
            record.nit_ci =  nit_ci
            record.complement =  complement
            
    def getNameReazonSocial(self, to_xml = False):
        if to_xml:
            return html.escape(self.reazon_social)
        return self.reazon_social
    


    def get_invoice_lines(self): # Lineas de factura
        return self.invoice_line_ids.filtered( 
            lambda line : \
                line.display_type == 'product' and \
                not line.product_id.gif_product
        )
        

    
    def getCuf(self):
        return self.cuf or ''
    


    def getPartnerNit(self):
        return self.nit_ci
    


    def getInvoiceNumber(self):
        return int(self.invoice_number)
    

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
    

    
    invisible_for_move = fields.Boolean( compute='_compute_invisible_for_move' )
    
    @api.depends('move_type', 'edi_bo_invoice')
    def _compute_invisible_for_move(self):
        for record in self:
            record.invisible_for_move = record.move_type in record.invisible_for_moves() and record.edi_bo_invoice
    
    def invisible_for_moves(self):
        return ['out_invoice']
    
    
    def getCompanyName(self, to_xml = False):
        reazon_social = self.company_id.partner_id.getNameReazonSocial()
        return escape(reazon_social) if to_xml else reazon_social
    