# -*- coding:utf-8 -*-

from odoo import api, models, fields

class AccountMoveLine(models.Model):
    
    _inherit = ['account.move.line']
    
    def get_amount_debit(self) -> float:
        return float(self.debit)
    
    def get_amount_credit(self) -> float:
        return float(self.credit)
    
    def get_amount_currency(self) -> float:
        return float(self.amount_currency)
    
    
    