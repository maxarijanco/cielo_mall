# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from xml.sax.saxutils import escape
from decimal import Decimal, ROUND_HALF_UP
import html

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']

    def decimalbo(self)->int:
        "Precicion Decimales"
        if self.move_id.document_type_id and self.move_id.document_type_id.getCode() in [24,47]:
            return 10
        return 2

    def getQuantity(self):
        return round(self.quantity, self.decimalbo())
    

    def getPriceUnit(self):
        return round( (self.price_unit * (1/self.currency_rate))  , self.decimalbo())
        # if self.move_id.document_type_id.getCode() not in [3, 4]:
        #     amount = round( (self.price_unit * (1/self.currency_rate))  , 2)
        # return amount
    
    def amountBase(self):
        return self.getQuantity() * self.getPriceUnit()

    def getSubTotal(self):
        amount = self.roundingUp( self.amountBase() - self.getAmountDiscount() , self.decimalbo())
        return  amount
    
    def getSpeciality(self):
        if self.product_id.categ_id:
            return self.product_id.categ_id.name
        return False
    
    item_number = fields.Integer(
        string='Nro. item',
        readonly=True
    )
    
    def getItemNumber(self):
        if self.item_number > 0:
            return self.item_number
        raise UserError(f"Producto{self.product_id.name}, no tiene el nro item asignado.")
    


    

    def getDescription(self, to_xml = False):
        description : str = self.name
        description = description.replace('\n', ' ').replace('\r', '')
        if to_xml:
            return html.escape(description)
        return description
    
    

    
    @api.model
    def roundingUp(self, value, precision):
        #factor = 10 ** precision
        #return (value * factor + 0.5) // 1 / factor
        return float(Decimal(str(value)).quantize(Decimal('1.' + '0' * precision), rounding=ROUND_HALF_UP))



    
  

    # ---------------------------
    
    