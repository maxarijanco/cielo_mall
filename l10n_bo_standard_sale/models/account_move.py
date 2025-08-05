# -*- coding:utf-8 -*-

from odoo import api, models, fields

class AccountMove(models.Model):
    
    _inherit = ["account.move"]

    def delete_standard_sale_line(self):
        for record in self:
            standard_sale_line = record.env['l10n.bo.standard.sale.line'].search([('invoice_id','=', record.id)], limit=1)
            if standard_sale_line:
                standard_sale_line.unlink()
        
    def unlink(self):
        for record in self:
            record.delete_standard_sale_line()
        result = super(AccountMove, self).unlink()
        return result
    
    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for record in self:
            record.delete_standard_sale_line()
        return res
    

    def _getAmountCeroRate(self):
        if self.document_type_id.getCode() in [8]:
            return self.getAmountTotal()
        return 0
    
    def _getAmountTotal(self):
        return round(self.getAmountTotal() + round(self.getAmountDiscount() + self.getAmountLineDiscount(), 2) + self.getAmountGiftCard(), 2)
    
    def _getAmountIce(self):
        if self.document_type_id.getCode() in [14]:
            return self.getAmountSpecificIce() + self.getAmountPercentageIce()
        return 0