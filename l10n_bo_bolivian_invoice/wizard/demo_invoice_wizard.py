# -*- coding:utf-8 -*- 
from odoo import models, fields

from odoo.exceptions import UserError, ValidationError



class DemoInvoiceWizard(models.TransientModel):
    _name = "demo.invoice.wizard"
    _description = "Generador de facturas para PILOTO (BO)"


    
    name = fields.Many2one(
        string='Punto de venta (BO)',
        comodel_name='l10n.bo.pos',
        required=True,
        readonly=True 
    )

    
    type = fields.Selection(
        string='Tipo',
        selection=[('invoice', 'Facturas'), ('package', 'Paquetes')],
        default='invoice',
        required=True
    )
    
    
    partner_id = fields.Many2one(
        string='Cliente',
        comodel_name='res.partner',
    )

    
    branch_office_id = fields.Many2one(
        string='Sucursal (BO)',
        comodel_name='l10n.bo.branch.office',
        related='name.branch_office_id',
        readonly=True,
        store=True
    )
    
    
    journal_id = fields.Many2one(
        string='Diario',
        comodel_name='account.journal',
        domain=[('type','=','sale'), ('bo_edi','=',True)],
        default=lambda self: self.getDefaultJournal()
    )

    def getDefaultJournal(self):
        journal_id = self.env['account.journal'].search([('type','=','sale'), ('bo_edi','=',True)], limit=1)
        return journal_id.id if journal_id else False

    
    demo_invoice_line_ids = fields.One2many(
        string='Lineas de facturas para pruebas',
        comodel_name='demo.invoice.line.wizard',
        inverse_name='demo_invoice_id',
    )

    
    
    demo_invoice_cancellation_line_ids = fields.One2many(
        string='Lineas de anulaciones de facturas de pruebas',
        comodel_name='demo.invoice.cancellation.line.wizard',
        inverse_name='demo_invoice_id',
    )

    demo_invoice_reversion_line_ids = fields.One2many(
        string='Lineas de reversion de facturas de pruebas',
        comodel_name='demo.invoice.reversion.line.wizard',
        inverse_name='demo_invoice_id',
    )

    
    
    demo_invoice_package_line_ids = fields.One2many(
        string='Lineas de paquetes',
        comodel_name='demo.invoice.package.line.wizard',
        inverse_name='demo_invoice_id',
    )

    def validate_document_types(self):
        available_docs = self.env['account.move'].getAvailableDocument()
        for line in self.demo_invoice_line_ids:
            if line.document_type.getCode() not in available_docs:
                raise UserError(f'{line.document_type.name} no esta implementado')
    
    def action_done(self):
        self.validate_document_types()
        if self.type == 'invoice':
            if self.demo_invoice_line_ids:
                if self.partner_id:
                    for line_id in self.demo_invoice_line_ids:
                        line_id.create_demo_invoices()
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': f'MENSAJE',
                            'message': f'Se necesita un cliente',
                            'sticky': False,
                        }
                    }

            for line_id in self.demo_invoice_cancellation_line_ids:
                line_id.action_cancellation_demo_invoices()

            for line_id in self.demo_invoice_reversion_line_ids:
                line_id.action_reversion_demo_invoices()
        
        elif self.type == 'package':
            if self.partner_id:
                for line_id in self.demo_invoice_package_line_ids:
                    line_id.action_invoice_package_line()

            else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': f'MENSAJE',
                            'message': f'Se necesita un cliente',
                            'sticky': False,
                        }
                    }
        
        

        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
