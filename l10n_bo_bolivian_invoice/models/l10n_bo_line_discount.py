# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

from odoo.tools import frozendict, formatLang, format_date, float_is_zero, Query


import logging
_logger = logging.getLogger(__name__)


# ELIMINAR MODELO
class LineDiscount(models.TransientModel):
    _name = 'line.discount'
    _description ="Descuento por linea"

    
    
    
    name = fields.Many2one(
        string='Linea de factura',
        comodel_name='account.move.line',
    )

    
    type = fields.Selection(
        string='Tipo',
        selection=[('amount', 'Monto'), ('percentage', 'Porcetaje')],
        default='amount',
        required=True
    )

    
    amount = fields.Float(
        string='Monto',
    )

    
    percentage = fields.Float(
        string='Porcentaje',
    )
    
    def action_done(self):
        self.discounting()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('percentage')
    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            if record.type == 'percentage':
                amount = (record.name.quantity * record.name.price_unit)  * (record.percentage / 100)
                self.write({'amount': amount})
    

    def discounting(self):
        if self.name:
            if self.type == 'amount':
                self.name.write({'proportional_discount' : self.amount / self.name.quantity, 'amount_discount' : self.amount, 'discount' : 0})
            else:
                self.name.write({'proportional_discount' : 0, 'amount_discount' : 0, 'discount' : self.percentage})
            #self.name._amount_discount()
    


class AccountMoveLineBase(models.Model):
    _inherit = ['account.move.line']

    
    
    
    proportional_discount = fields.Float(
        string='Descuento proporcional',
    )
    
    prorated_line_discount = fields.Float(
        string='Descuento total prorateado',
        help='Acumula el descuento por linea correspondiente + el descuento global prorateado',
        digits=(16, 10),
        
        readonly=False
    )
    
    def line_discount_wizard(self):
        if self.display_type == 'product' and not self.product_id.gif_product and self.move_id.document_type_id and self.move_id.document_type_id.getCode() not in [24, 47]:
            return {
                'name': 'Descuento por linea',
                'type': 'ir.actions.act_window',
                'res_model': 'line.discount',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': self.id
                }
            }
    
    # ELIMINAR METODO
    def apportionment_partial(self):
        total_venta = self.move_id.getAmountSubTotal() # subTotalBase()
        total_venta /= self.move_id.currency_id.getExchangeRate()
        _logger.info(f'Total venta: {total_venta}')
            #  self.getSubTotal_14()
        base = self.getSubTotal() / self.move_id.currency_id.getExchangeRate() #( self.quantity * (self.getPriceUnit() / self.move_id.currency_id.getExchangeRate()) ) - (self.getAmountDiscount() / self.move_id.currency_id.getExchangeRate())
        porcentaje_descuento_prorrateado = ((self.move_id.getAmountDiscount() / self.move_id.currency_id.getExchangeRate() ) * base) / total_venta
        return porcentaje_descuento_prorrateado

    # ELIMINAR METODO
    def ap(self):
        porcentaje_descuento_prorrateado = self.apportionment_partial()
        apportionment = porcentaje_descuento_prorrateado + (self.getAmountDiscount() / self.move_id.currency_id.getExchangeRate())
                
        return apportionment 

    def apportionment(self, total_venta, global_discount):
        if self.getSubTotal() > 0:
            if self.move_id.document_type_id.getCode() in [14]:
                _logger.info('Proceso de prorrateo')
                #total_venta = self.getAmountSubTotalWithOutICE()# + self.move_id.getAmountLineDiscount()

                #total_venta /= self.move_id.currency_id.getExchangeRate()
                #_logger.info(f'Total venta: {total_venta}')

                #base = self.getSubTotal() / self.move_id.currency_id.getExchangeRate() #( self.quantity * (self.getPriceUnit() / self.move_id.currency_id.getExchangeRate()) ) - (self.getAmountDiscount() / self.move_id.currency_id.getExchangeRate())
                #raise UserError(base)
            
                #base += self.getSpecificIce() + self.getPercentageIce()
                
                
                #porcentaje_descuento_prorrateado = ((self.move_id.getAmountDiscount() / self.move_id.currency_id.getExchangeRate() ) * base) / total_venta
                #porcentaje_descuento_prorrateado = self.apportionment_partial()
                apportionment = self.ap() #porcentaje_descuento_prorrateado + (self.getAmountDiscount() / self.move_id.currency_id.getExchangeRate())
                self.write(
                    {
                        'prorated_line_discount' : round(apportionment, 10)
                    }
                )

            else:
                #total_venta = (self.move_id.amountCurrency() * self.move_id.currency_id.getExchangeRate()) + self.move_id.getAmountDiscount() + self.move_id.getAmountLineDiscount()
                #total_venta = amount_subtotal
                #porcentaje_descuento_prorrateado = self.move_id.getAmountDiscount() / total_venta
                #porcentaje_descuento_prorrateado = self.getSubTotal() * global_discount #self.move_id.getAmountDiscount()
                #apportionment = round(porcentaje_descuento_prorrateado * (self.getSubTotal() + self.getAmountDiscount() ), 2)
                #apportionment = (self.getSubTotal() * global_discount) / total_venta #round(porcentaje_descuento_prorrateado / total_venta, 10)
                #apportionment = self.ap() #self.getAmountDiscount()
                #self.prorated_line_discount = apportionment

                total_venta /= 1/self.currency_rate
                base = self.getSubTotal() / (1/self.currency_rate)
                global_discount /= 1/self.currency_rate

                prorated_line_discount = ( base * global_discount) / total_venta

                self.prorated_line_discount = prorated_line_discount
                #self.prorated_line_discount += self.getAmountDiscount()
                _logger.info(f'Descuento aplicado: {self.prorated_line_discount}')


    # def _get_discount_from_fixed_discount(self):
    #     self.ensure_one()
    #     currency = self.currency_id or self.company_id.currency_id
    #     if float_is_zero(self.proportional_discount, precision_rounding=currency.rounding):
    #         return 0.0
    #     return (self.proportional_discount / self.price_unit) * 100
    
    

    # @api.depends('quantity', 'discount','amount_discount', 'price_unit', 'tax_ids', 'currency_id')
    # def _compute_totals(self):
    #     for line in self:
    #         if line.proportional_discount>0:
                
    #             if line.display_type != 'product':
    #                 line.price_total = line.price_subtotal = False
    #             # Compute 'price_subtotal'.
    #             line_discount_price_unit = line.price_unit - (line.amount_discount/ line.quantity) # * HERE
    #             subtotal = line.quantity * line_discount_price_unit

    #             # Compute 'price_total'.
    #             if line.tax_ids:
    #                 taxes_res = line.tax_ids.compute_all(
    #                     line_discount_price_unit,
    #                     quantity=line.quantity,
    #                     currency=line.currency_id,
    #                     product=line.product_id,
    #                     partner=line.partner_id,
    #                     is_refund=line.is_refund,
    #                 )
    #                 line.price_subtotal = taxes_res['total_excluded']
    #                 line.price_total = taxes_res['total_included']
    #             else:
    #                 line.price_total = line.price_subtotal = subtotal
                    
    #         else:
    #             super(AccountMoveLineBase, line)._compute_totals()


    

    # @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    # def _compute_all_tax(self):
    #     for line in self:
    #         sign = line.move_id.direction_sign
    #         if line.display_type == 'tax':
    #             line.compute_all_tax = {}
    #             line.compute_all_tax_dirty = False
    #             continue
    #         if line.display_type == 'product' and line.move_id.is_invoice(True):
    #             if line.proportional_discount>0:
    #                 amount_currency = sign * (line.price_unit - line.fixed_amount_total_discount)
    #             else:
    #                 amount_currency = sign * line.price_unit * (1 - line.discount / 100)
    #             # amount_currency = sign * line.price_unit * (1 - line.discount / 100)
    #             handle_price_include = True
    #             quantity = line.quantity
    #         else:
    #             amount_currency = line.amount_currency
    #             handle_price_include = False
    #             quantity = 1
    #         compute_all_currency = line.tax_ids.compute_all(
    #             amount_currency,
    #             currency=line.currency_id,
    #             quantity=quantity,
    #             product=line.product_id,
    #             partner=line.move_id.partner_id or line.partner_id,
    #             is_refund=line.is_refund,
    #             handle_price_include=handle_price_include,
    #             include_caba_tags=line.move_id.always_tax_exigible,
    #             fixed_multiplicator=sign,
    #         )
    #         rate = line.amount_currency / line.balance if line.balance else 1
    #         line.compute_all_tax_dirty = True
    #         line.compute_all_tax = {
    #             frozendict({
    #                 'tax_repartition_line_id': tax['tax_repartition_line_id'],
    #                 'group_tax_id': tax['group'] and tax['group'].id or False,
    #                 'account_id': tax['account_id'] or line.account_id.id,
    #                 'currency_id': line.currency_id.id,
    #                 'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
    #                 'tax_ids': [(6, 0, tax['tax_ids'])],
    #                 'tax_tag_ids': [(6, 0, tax['tag_ids'])],
    #                 'partner_id': line.move_id.partner_id.id or line.partner_id.id,
    #                 'move_id': line.move_id.id,
    #                 'display_type': line.display_type,
    #             }): {
    #                 'name': tax['name'] + (' ' + ('(Descuento)') if line.display_type == 'epd' else ''),
    #                 'balance': tax['amount'] / rate,
    #                 'amount_currency': tax['amount'],
    #                 'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
    #             }
    #             for tax in compute_all_currency['taxes']
    #             if tax['amount']
    #         }
    #         if not line.tax_repartition_line_id:
    #             line.compute_all_tax[frozendict({'id': line.id})] = {
    #                 'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
    #             }


            
    

    




class AccountMove(models.Model):
    _inherit = ['account.move']
    

    def getAmountLineDiscount(self):
        amount = 0
        for line in self.invoice_line_ids:
            if not line.product_id.global_discount:
                amount += line.getAmountDiscount()
        return amount
    
        return 0
    
    
    
    def getAmountLineDiscountItem(self, item):
        for line in self.invoice_line_ids:
            if line.item_number == item:
                return line.getAmountDiscount()
        return 0
    

    