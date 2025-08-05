# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']
    
    def getPriceUnit2(self):
        amount = self.price_unit
        amount = round(amount* self.move_id.currency_id.getExchangeRate(),2)
        # if self.move_id.document_type_id.getCode() not in [3, 4]:
        #     amount = round( (self.price_unit * (1/self.currency_rate))  , 2)
        return amount
    
    def getSubTotal2(self, decimal = 2 ):
        amount = self.roundingUp( (self.quantity * self.getPriceUnit2() ) - self.getAmountDiscount() , decimal)
        return  amount