# -*- coding:utf-8 -*-

from odoo import api, models, fields
from num2words import num2words

class AccountMove(models.Model):
    _inherit = ['account.move']
    

    
        
    def getAmountCredit(self) -> float:
        for record in self:
            return sum( [ line_id.credit for line_id in record.line_ids ] )   


    def getAmountDebit(self) -> float:
        for record in self:
            return sum( [ line_id.debit for line_id in record.line_ids ] )   
    
    def getAmountCurrency(self) -> float:
        for record in self:
            return round(sum( [ line_id.amount_currency for line_id in record.line_ids ] ), 2)   
    

    def getLiteralVoucher(self) -> str:
        for record in self:
            amount = round(abs(record.amount_total_signed), 2)
            parte_entera = int(amount)
            parte_decimal = int( round((amount - parte_entera),2) *100)
            parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
            _literal : str = str(num2words(parte_entera, lang='es') + parte_decimal +'/100 ')
            _literal += record.company_id.currency_id.full_name
            return _literal.upper()
        
    def getLiteralCurrency(self) -> str:
        amount = round(abs(self.amount_total_in_currency_signed), 2)
        parte_entera = int(amount)
        parte_decimal = int( round((amount - parte_entera),2) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        _literal : str = str(num2words(parte_entera, lang='es') + parte_decimal +'/100 ')
        _literal += self.currency_id.full_name
        return _literal.upper()
        
        
    