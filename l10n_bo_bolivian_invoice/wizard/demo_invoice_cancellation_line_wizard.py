# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class DemoInvoiceCancellationLineWizard(models.TransientModel):
    _name="demo.invoice.cancellation.line.wizard"
    _description = 'Asistente de lineas de anulacion  de facturas de prueba (BO)'

    
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
        string='Razón',
        comodel_name='l10n.bo.cancellation.reason',
        required=True
        
    )
    
    demo_invoice_id = fields.Many2one(
        string='Demo facturas',
        comodel_name='demo.invoice.wizard',
    )

    def action_cancellation_demo_invoices(self):
        if self.quantity>0:
            PARAMS = [
                ('state','=','posted'),
                ('edi_bo_invoice','=',True),
                ('edi_state','=','VALIDADA'),
                ('pos_id.code','=',self.demo_invoice_id.name.code),
                ('document_type_id.name','=',self.document_type.id),
                ('company_id','=',self.demo_invoice_id.name.company_id.id),
                
            ]
            to_continue = False
            
            if self.document_type.getCode() in [1,2,3,4,6,8,11,13,14,16,17,28]:
                PARAMS.append(('move_type','=','out_invoice'))
                to_continue = True
            elif self.document_type.getCode() in [24, 47, 48]:
                PARAMS.append(('move_type','=','out_refund'))
                to_continue = True
            
            
            if to_continue:
                invoice_ids = self.env['account.move'].search(PARAMS, limit=self.quantity)

                
                for invoice_id in invoice_ids:
                    cancellation_reazon_id = self.env['cancellation.reason'].create({
                        'account_move_id': invoice_id.id,
                        'purchase_sale_reason_id' : self.reason_id.id,
                        'adjust_document_reason_id' : self.reason_id.id,
                    })
                    if cancellation_reazon_id:
                        #raise UserError(cancellation_reazon_id.account_move_id.name)
                        cancellation_reazon_id.cancellation()
        else:
            raise UserError('Debe generar cantidades mayores a 0')