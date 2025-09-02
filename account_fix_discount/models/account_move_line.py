# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import frozendict

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_discount_percentage(self):
        "Get discount or discountFixed in percentage. Ej 20 -> 0.0026% "
        if self.discount != 0:
            return self.discount
        elif self.amount_discount != 0 and self.quantity !=0 and self.price_unit!=0:
            return ( self.amount_discount / (self.quantity * self.price_unit)) * 100
        return 0
    
    def get_price_unit_discounted(self):
        "Get PriceUnit Discounted. Ej PriceUnit=5000 - Disc 20% =  4999.87"
        return  self.price_unit * (1 - ( self.get_discount_percentage() / 100.0))
    
    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                amount_currency = sign * line.get_price_unit_discounted()
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                }): {
                    'name': tax['name'],
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'amount_discount')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.get_price_unit_discounted() 
            subtotal = line.quantity * line_discount_price_unit
            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.is_refund,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

    amount_discount = fields.Float(
        string="Desc. fijo",
        default=0.0,
        digits='Discount Fix',
        help="Descuento = (Descuento Fijo / (Cantidad X Precio)) * 100",
    )


    @api.onchange("amount_discount")
    def _onchange_amount_discount(self):
        """Compute the fixed discount based on the discount percentage."""
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.env.context = self.with_context(ignore_discount_onchange=True).env.context
        self.discount = 0.0

    @api.onchange("discount")
    def _onchange_discount(self):
        """Compute the discount percentage based on the fixed discount.
        Ignore the onchange if the fixed discount is already set.
        """
        if self.env.context.get("ignore_discount_onchange"):
            return
        self.env.context = self.with_context(ignore_discount_onchange=True).env.context
        self.amount_discount = 0.0

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """
        self.ensure_one()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1
        dis = self.discount
        if self.amount_discount:
            if int(self.price_unit) != 0:
                dis = (self.amount_discount * 100) / self.price_unit
            else:
                dis = 0
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit if is_invoice else self.amount_currency,
            quantity=self.quantity if is_invoice else 1.0,
            discount=dis,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            price_subtotal=sign * self.amount_currency,
            is_refund=self.is_refund,
            rate=(abs(self.amount_currency) / abs(self.balance)) if self.balance else 1.0 )
