# -*- codin:utf-8 -*-

from odoo import api, models, fields
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)



class DemoInvoicePackageLine(models.TransientModel):
    _name = "demo.invoice.package.line.wizard"
    _description = "Linea de paquetes de facturas de prueba (BO)"

    
    quantity = fields.Integer(
        string='Paquetes',
        default=1,
        help='Cantidad de paquetes',
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

    product_id = fields.Many2one(
        string='Producto',
        comodel_name='product.product',
        required=True
    )

    
    qty = fields.Integer(
        string='Facturas',
        default=1,
        help='Cantidad de facturas por paquete'
    )
    
    event_id = fields.Many2one(
        string='Evento',
        comodel_name='l10n.bo.significant.event',
        required=True
    )

    def set_event(self):
        self.demo_invoice_id.name.event_id.write({'event_id' : self.event_id.id})
        last_event = self.env['significant.event'].search([('id','=',self.demo_invoice_id.name.event_id.id-1)], limit=1)
        if last_event and last_event.date_end == self.demo_invoice_id.name.event_id.date_init:
            _logger.info("Se ha cambiado la fecha de un evento signficativo")
            self.demo_invoice_id.name.event_id.write({'date_init' : self.demo_invoice_id.name.event_id.date_init + timedelta(seconds=1)})
            return self.demo_invoice_id.name.event_id.date_init
        return False

    def action_invoice_package_line(self):
        i = 0
        while i < self.quantity:
            self.demo_invoice_id.name.action_offline()
            date_time_now = self.set_event()
            
            demo_invoice_id =  self.env['demo.invoice.line.wizard'].create(
                {
                    'demo_invoice_id' : self.demo_invoice_id.id,
                    'document_type' : self.document_type.id,
                    'quantity' : self.qty,
                    'product_id' : self.product_id.id,
                    'confirm' : True
                }
            )
            if demo_invoice_id:
                demo_invoice_id.create_demo_invoices(date_time_now)
                self.demo_invoice_id.name.action_online()
            i += 1

            if self.event_id.getCode() in [5,6,7]:
                for cafc_id in self.document_type.cafc_ids:
                    cafc_id.write({'actual_sequence' : cafc_id.from_sequence})