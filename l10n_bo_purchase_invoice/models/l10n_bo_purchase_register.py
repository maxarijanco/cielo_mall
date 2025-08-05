# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import xlwt
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)



class L10nBoPurchaseRegister(models.Model):
    _name='l10n.bo.purchase.register'
    _description="Registro de compra (BO)"

    
    name = fields.Char(
        string='Nombre',
        readonly=True 
    )
    
    
    date_from = fields.Date(
        string='Desde',
    )
    
    date_to = fields.Date(
        string='Hasta',
    )
    
    
    purchase_register_line_ids = fields.One2many(
        string='Lineas de registro de compra',
        comodel_name='l10n.bo.purchase.register.line',
        inverse_name='purchase_register_id',
    )
    
    def get_preview_registers(self, PARAMS : list = []):
        #PARAMS.append(('invoice_id.bo_purchase_edi_anuled','=',False))
        #PARAMS.append(('invoice_id.bo_purchase_edi_validated','=',True))
        
        records =  self.env['l10n.bo.purchase.register.line'].search(PARAMS)
        for record in records:
            record.write({'purchase_register_id': self.id})
    
    def get_invoice_ids(self):
        PARAMS = [
            ('move_type','=','in_invoice'),
            ('state','=','posted'),
            #('bo_purchase_edi_validated','=',True),
            #('bo_purchase_edi_anuled','=',False),
            ('bo_purchase_edi','=',True),
        ]
        preview_params = [('company_id','=',self.env.company.id)]
        if self.date_from and self.date_to:
            PARAMS.append(('invoice_date','>=', self.date_from))
            PARAMS.append(('invoice_date','<=', self.date_to))
            preview_params += [('dui_dim_date','>=', self.date_from), ('dui_dim_date','<=', self.date_to)]
        
        self.get_preview_registers(preview_params)
        
            
        return self.env['account.move'].search(
            PARAMS,
            order='invoice_date desc'
        )
    
    def create_invoice_records(self, invoice_ids):
        new_records = []
        for invoice_id in invoice_ids:
            _logger.info(f'Factura: {invoice_id.name}, ID: {invoice_id.id}')
            params = {
                'invoice_id'    :  invoice_id.id,
                'name'          :  invoice_id.get_purchase_sequence(),
                'specification' :  1,
                'nit'        :  invoice_id.getEmisorNIT(),
                'reazon_social' :  invoice_id.getRazonSocialSupplier(),
                'autorization_code' :  invoice_id.getCufSupplier(),
                'invoice_number'  :  invoice_id.getInvoiceBillNumber(),
                'dui_dim_number' : invoice_id.getDUIDIMNumber(),
                'dui_dim_date' : invoice_id.invoice_date,
                'amount_total'  :  invoice_id.getAmountTotalSupplier(),
                'amount_ice'    :  invoice_id.getAmountIceFromSupplier(),
                'amount_iehd'   :  invoice_id.getAmountIehdFromSupplier(),
                'amount_ipj'    :  invoice_id.getAmountIpjFromSupplier(),
                'amount_rate'   :  invoice_id.getAmountRateFromSupplier(),
                'amount_no_iva' :  invoice_id.getAmountNoIvaFromSupplier(),
                'amount_exempt' :  invoice_id.getAmountExemptFromSupplier(),
                'amount_cero_rate'   :  invoice_id.getAmountZeroRateFromSupplier(),
                'amount_subtotal' : invoice_id.getAmountSubTotalSupplier(),
                'amount_discount' : invoice_id.getAmountDisccountSupplier(),
                'amount_gift_card'    :  invoice_id.getAmountGifCardSuppllier(),
                'amount_base_fiscal_credit' : invoice_id.getAmountOnIvaSupplier(),
                'amount_fiscal_credit' : round(invoice_id.getAmountOnIvaSupplier() * 0.13, 2),
                'purchase_type' : invoice_id.getPurchaseType(),
                'control_code'  : invoice_id.getControlCodeSupplier(),

                'purchase_register_id' : self.id,
            }
            new_records.append(params)
        if new_records:
            self.env['l10n.bo.purchase.register.line'].create(new_records)

    
    def clean_register_olds(self):
        for record in self.purchase_register_line_ids:
            record.write({'purchase_register_id': False})

    def action_update(self):
        self.clean_register_olds()
        invoice_ids = self.get_invoice_ids()
        _logger.info(f"FACTURAS: {invoice_ids}")
        if invoice_ids:
            new_lines = []
            l10n_bo_rc_ids = [ line.invoice_id.id for line in self.purchase_register_line_ids if line.invoice_id ]
            for invoice_id in invoice_ids:
                if invoice_id.id not in l10n_bo_rc_ids:
                    new_lines.append(invoice_id)
            
            if new_lines:
                self.create_invoice_records(new_lines)

    def get_column_fields(self) -> list:
        fields = []
        for field_name, field in self.purchase_register_line_ids._fields.items():
            if field_name not in ('name','specification','nit','reazon_social','autorization_code', 'invoice_number', 'dui_dim_number','dui_dim_date','amount_total','amount_ice','amount_iehd','amount_ipj','amount_rate','amount_no_iva','amount_exempt','amount_cero_rate','amount_subtotal','amount_discount','amount_gift_card','amount_base_fiscal_credit','amount_fiscal_credit','purchase_type','control_code'):
                continue
            field_label = {
                'campo': field_name,
                'string': field.string,
                'type': field.type
            }
            fields.append(field_label)
        return fields


    def generate_excel_file(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet('Registros de Compras')
        bold_style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        bold_style.font = font
        headers = self.get_column_fields() 
        if headers:
            for col, header in enumerate(headers):
                worksheet.write(0, col, header.get('string'), bold_style)
            row = 1
            for record in self.purchase_register_line_ids:
                for i in range(len(headers)):
                    value = getattr(record,headers[i].get('campo'))
                    if not value:
                        _type = headers[i].get('type')
                        if _type == 'float':
                            value = 0.00
                        elif _type == 'char':
                            value = ''
                    worksheet.write(row, i, value)
                row += 1
            excel_buffer = BytesIO()
            workbook.save(excel_buffer)
            excel_buffer.seek(0)
            excel_base64 = base64.b64encode(excel_buffer.getvalue())
            excel_buffer.close()
            return excel_base64
        raise UserError('No se contraron campos para las columnas')
    

    excel_file = fields.Binary(
        string="Archivo Excel",
    )

    def download_excel_file(self):
        if len(self.purchase_register_line_ids)>0:
            self.write({'excel_file': False})
            excel_data = self.generate_excel_file()
            self.write({'excel_file': excel_data})
            return {
                'type': 'ir.actions.act_url',
                'url': f'web/content/?model={self._name}&id={self.id}&field=excel_file&download=true&filename=RegistroCompras.xls',
                'target': 'self',
            }