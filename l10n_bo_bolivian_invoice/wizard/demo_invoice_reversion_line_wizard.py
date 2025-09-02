# -*- coding:utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError

class DemoInvoiceCancellationLineWizard(models.TransientModel):
    _name="demo.invoice.reversion.line.wizard"
    _description = 'Asistente de lineas de reversion de facturas de prueba (BO)'

    
    document_type = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.document.type',
        required=True,
        domain=[('use','=',True)]   
    )

    
    quantity = fields.Integer(
        string='Estimado',
        default=1,
        help='Se buscará la cantidad estimada establecida por el usuario.'
    )

    reason_id = fields.Many2one(
        string='Referencia',
        comodel_name='l10n.bo.cancellation.reason',
        required=True,
        help='Se buscara los documentos eliminados con la razon espesificada.'
    )
    
    demo_invoice_id = fields.Many2one(
        string='Demo facturas',
        comodel_name='demo.invoice.wizard',
    )

    def action_reversion_demo_invoices(self):
        if self.quantity>0:
            PARAMS = [
                ('state','=','cancel'),
                ('edi_bo_invoice','=',True),
                ('edi_state','=','ANULACION CONFIRMADA'),
                ('pos_id','=',self.demo_invoice_id.name.id),
                ('document_type_code','=',self.document_type.codigoClasificador),
                ('cancellation_reason_id.codigoClasificador','=', self.reason_id.codigoClasificador)
            ]
            to_continue = False
            
            if self.document_type.getCode() in [1,2,3,4,6,8,11,13,14,16,17,28]:
                PARAMS.append(('move_type','=','out_invoice'))
                to_continue = True
            elif self.document_type.getCode() in [24,47, 48]:
                PARAMS.append(('move_type','=','out_refund'))
                to_continue = True
            
            
            if to_continue:
                invoice_ids = self.env['account.move'].search(PARAMS, limit=self.quantity)
                for invoice_id in invoice_ids:
                    invoice_id.action_reversion()
        else:
            raise UserError('Debe generar cantidades mayores a 0')