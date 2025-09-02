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

    
    edi_bo_invoice = fields.Boolean(
        related='move_id.edi_bo_invoice',
        readonly=True,
        store=True
    )

    
    line_reversed_id = fields.Many2one(
        string='Linea revertida',
        comodel_name='account.move.line'
    )
    

    @api.onchange('quantity','price_unit')
    def _onchange_quantity_price_unit(self):
        if self.line_reversed_id:
            _logger.info(f'Descuento fijo anterior: {self.line_reversed_id.get_discount_fix()}')
            previous_amount_base = self.line_reversed_id.quantity * self.line_reversed_id.price_unit
            _logger.info(f'Monto base anterior: {previous_amount_base}')
            discount_fix_prorated = (self.line_reversed_id.get_discount_fix() * (self.quantity * self.price_unit)) / previous_amount_base
            _logger.info(f'Descuento fijo prorateado: {discount_fix_prorated}')
            
            amount_subtotal = (self.quantity * self.price_unit) - discount_fix_prorated

            discount_global_prorated = (self.line_reversed_id.prorated_line_discount * amount_subtotal) / (previous_amount_base - self.line_reversed_id.get_discount_fix())
            _logger.info(f'Descuento global prorateado: {discount_global_prorated}')
            
            self.prorated_line_discount = discount_global_prorated
            self.amount_discount = discount_fix_prorated + discount_global_prorated #(self.line_reversed_id.prorated_line_discount * self.amountBase() ) / self.line_reversed_id.amountBase()

    def get_prorated_line_discount(self):
        amount = self.prorated_line_discount * self.currency_id.getExchangeRate()
        # if self.move_type in ['out_refund'] or self.line_reversed_id:
        #     amount = self.prorated_line_discount * self.currency_id.getExchangeRate()
        return amount
    
    def decimalbo(self)->int:
        "Precicion Decimales"
        if self.move_id.document_type_id and self.move_id.document_type_id.getCode() in [24,47]:
            return 10
        return 2

    def getQuantity(self):
        return round(self.quantity, self.decimalbo())
    

    def getPriceUnit(self):
        amount = round( (self.price_unit * (1/self.currency_rate))  , self.decimalbo())
        return amount
        # if self.move_id.document_type_id.getCode() not in [3, 4]:
        #     amount = round( (self.price_unit * (1/self.currency_rate))  , 2)
        # return amount
    
    def amountBase(self):
        amount = self.getQuantity() * self.getPriceUnit()
        return amount

    def getSubTotal(self):
        amount = self.roundingUp( self.amountBase() - self.getAmountDiscount() , self.decimalbo())
        #raise UserError(f'{self.getQuantity()} | {self.getPriceUnit()} | {self.getAmountDiscount()} | {self.decimalbo()} | monto: {amount}')
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
    
    def get_discount_fix(self):
        amount = self.amount_discount
        amount -= self.prorated_line_discount if self.line_reversed_id else 0

        if self.discount!=0:
            amount = (self.quantity * self.price_unit)  * (self.get_discount_percentage() / 100)
        return amount
        
    def getAmountDiscount(self):
        amount = self.get_discount_fix()
        amount *= (1/self.currency_rate)
        return self.roundingUp(amount, self.decimalbo() )
    
    def getTotalAmountDiscount(self):
        amount = self.getAmountDiscount() + self.get_prorated_line_discount()
        return self.roundingUp(amount, self.decimalbo() )
        

    
    @api.model
    def roundingUp(self, value, precision):
        value = Decimal(str(round(value, precision + 3)))  # precorrección
        return float(value.quantize(Decimal('1.' + '0' * precision), rounding=ROUND_HALF_UP))
        #return float(Decimal(str(value)).quantize(Decimal('1.' + '0' * precision), rounding=ROUND_HALF_UP))
        #factor = 10 ** precision
        #return (value * factor + 0.5) // 1 / factor
        


    
  

    # ---------------------------------------------------------------------------------------------------