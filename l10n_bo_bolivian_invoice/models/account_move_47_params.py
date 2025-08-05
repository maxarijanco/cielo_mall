# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from num2words import num2words

import logging
_logger = logging.getLogger(__name__)



class AccountMove47Params(models.Model):    
    _inherit = ['account.move']
    
    def credit_debit_note_discount_format(self):
        cabecera = """<cabecera>"""
        cabecera += f"""<nitEmisor>{self.company_id.getNit()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getCompanyName()}</razonSocialEmisor>"""
        cabecera += f"""<municipio>{self.getMunicipality()}</municipio>"""
        cabecera += f"""<telefono>{self.getPhone()}</telefono>"""
        cabecera += f"""<numeroNotaCreditoDebito>{self.getInvoiceNumber()}</numeroNotaCreditoDebito>"""
        cabecera += f"""<cuf>{self.getCuf()}</cuf>"""
        cabecera += f"""<cufd>{self.getCufd()}</cufd>"""
        cabecera += f"""<codigoSucursal>{self.getBranchCode()}</codigoSucursal>"""
        cabecera += f"""<direccion>{self.getAddress()}</direccion>"""
        cabecera += f"""<codigoPuntoVenta>{self.getPosCode()}</codigoPuntoVenta>"""
        cabecera += f"""<fechaEmision>{self.getEmisionDate()}</fechaEmision>"""
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial(to_xml=True)}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.partner_id.getNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.partner_id.getComplement()}</complemento>""" if self.partner_id.complement else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.partner_id.vat}</codigoCliente>"""
        cabecera += f"""<numeroFactura>{self.getOriginalInvoiceNumber()}</numeroFactura>"""
        cabecera += f"""<numeroAutorizacionCuf>{self.getOriginalCuf()}</numeroAutorizacionCuf>"""
        cabecera += f"""<fechaEmisionFactura>{self.getOriginalInvoiceDate()}</fechaEmisionFactura>"""
        cabecera += f"""<montoTotalOriginal>{self.getOriginalAmount47()}</montoTotalOriginal>"""
        
        cabecera += f"""<descuentoAdicional>{self.reversed_entry_id.getAmountDiscount()}</descuentoAdicional>"""  if self.reversed_entry_id.getAmountDiscount()>0 else """<descuentoAdicional xsi:nil="true"/>"""
        
        cabecera += f"""<montoTotalDevuelto>{self.getAmountTotalReturned47()}</montoTotalDevuelto>"""
        #cabecera += f"""<montoTotalDevuelto>1000</montoTotalDevuelto>"""
        cabecera += f"""<montoDescuentoCreditoDebito>{self.getAmountTotalProrated()}</montoDescuentoCreditoDebito>""" if self.getAmountTotalProrated() > 0 else """<montoDescuentoCreditoDebito xsi:nil="true"/>"""
        #cabecera += f"""<montoDescuentoCreditoDebito>500</montoDescuentoCreditoDebito>"""
        cabecera += f"""<montoEfectivoCreditoDebito>{self.getAmountEffective47()}</montoEfectivoCreditoDebito>"""
        #cabecera += f"""<montoEfectivoCreditoDebito>130</montoEfectivoCreditoDebito>"""
        cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        cabecera += f"""<codigoDocumentoSector>{self.getDocumentSector()}</codigoDocumentoSector>"""
        cabecera += """</cabecera>"""
        
        detalle  = """"""
        
        
        for line in self.reversed_entry_id.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<nroItem>{line.getItemNumber()}</nroItem>"""

                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode(to_xml =True)}</codigoProducto>"""
                detalle += f"""<descripcion>{line.getDescription(to_xml =True)}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
                detalle += f"""<codigoDetalleTransaccion>1</codigoDetalleTransaccion>"""
                detalle += """</detalle>"""
        
        
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<nroItem>{line.getItemNumber()}</nroItem>"""
                
                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode(to_xml =True)}</codigoProducto>"""
                detalle += f"""<descripcion>{line.getDescription(to_xml =True)}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                #detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount_t2_47()}</montoDescuento>""" if line.getAmountDiscount_t2_47() > 0 else """<montoDescuento xsi:nil="true"/>"""
                
                detalle += f"""<subTotal>{line.getSubTotal_t2_47()}</subTotal>"""
                detalle += f"""<codigoDetalleTransaccion>2</codigoDetalleTransaccion>"""
                detalle += """</detalle>"""
        return cabecera + detalle

        
    
    def credit_debit_note_discount_format_computerized(self):
        _format = f"""<notaComputarizadaCreditoDebitoDescuento xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="notaComputarizadaCreditoDebitoDescuento.xsd">"""
        _format += self.credit_debit_note_discount_format()
        _format += f"""</notaComputarizadaCreditoDebitoDescuento>"""
        return _format
    

    def credit_debit_note_discount_format_electronic(self):
        _format = f"""<notaElectronicaCreditoDebitoDescuento xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="notaElectronicaCreditoDebitoDescuento.xsd">"""
        _format += self.credit_debit_note_discount_format()
        _format += f"""</notaElectronicaCreditoDebitoDescuento>"""
        return _format

    # def getAmountProrated(self, _item_number):
    #     for line in self.invoice_line_ids:
    #         if line.item_number == _item_number:
    #             return line.prorated_line_discount
    #     return 0
    
    def amountTotalOriginalPay47(self):
        amount = self.getOriginalAmount47() - self.reversed_entry_id.getAmountDiscount()
        return round(amount, 2)
    
    def getAmountTotalProrated(self):
        amount = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product and line.item_number > 0:
                amount += self.reversed_entry_id.getAmountProrated47(line.item_number)
        _logger.info(f'Suma total prorrateado: {amount}')
        #amount *= self.currency_id.getExchangeRate()
        return self.roundingUp(amount, self.decimalbo())

    def getAmountProrated47(self, item):
        for line in self.invoice_line_ids:
            if line.item_number == item:
                #raise UserError(f"PRORRATEADO: {line.prorated_line_discount}, DESCUENTO: {line.getAmountDiscount()}")
                return self.roundingUp(line.get_prorated_line_discount() - line.getAmountDiscount(), self.decimallinebo())
        return 0
        
    def getOriginalAmount47(self):
        amount = self.reversed_entry_id.getAmountSubTotal()
        #raise UserError(amount)
        return amount
    
    def getAmountSubtotal47(self):
        amount_subtotal = 0
        for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.gif_product:
                    amount_subtotal += line.getSubTotal_t2_47()
        return self.roundingUp(amount_subtotal, self.decimalbo())
            

    def getAmountTotalReturned47(self):
        #raise UserError(f'SUBTOTAL:{self.getAmountSubtotal47()}, - PRORRATEADO:{self.getAmountTotalProrated()}, DECIMALES: {self.decimalbo()}')
        return self.roundingUp(self.getAmountSubtotal47() - self.getAmountTotalProrated(), self.decimalbo())
    
    def getAmountEffective47(self):
        return self.roundingUp(self.getAmountTotalReturned47() * 0.13, self.decimalbo())
    

    def getBolivianLiteral47(self):
           
        amount_total = self.getAmountTotalReturned47() # * self.currency_id.getExchangeRate()
        
        if self.document_type_code in [14]:
            amount_total += self.getAmountSpecificIce() + self.getAmountPercentageIce()

        parte_entera = int(amount_total)
        parte_decimal = int( round((amount_total - parte_entera),2) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        return num2words(parte_entera, lang='es') + parte_decimal +'/100'

    def _post(self, soft=True):
        for record in self:
            record.item_number_assigned()
        res = super(AccountMove47Params, self)._post(soft = soft)
        return res
    

    def item_number_assigned(self):
        for record in self:
            if record.move_type == 'out_invoice':
                item = 1
                for line in record.invoice_line_ids:
                    if line.display_type == 'product' and not line.product_id.gif_product:
                        line.write({'item_number':item})
                        item += 1


    
    def _set_default_document_type(self):
        super(AccountMove47Params, self)._set_default_document_type()
        if self.reversed_entry_id and self.reversed_entry_id.document_type_id.getCode() == 1:
            if self.pos_id:
                #self.write({'document_type_id' : self.get_credit_debit_ice_id()}) 
                discount_lines = self.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.product_id and line.product_id.global_discount)
                if discount_lines:
                    discount_lines.unlink()
                    
                    for line in self.invoice_line_ids:
                        discount_line_id = self.env['line.discount'].create(
                            {
                                'name' : line.id,
                                'type' : 'amount',
                                'amount' : self.reversed_entry_id.getAmountProrated(line.getItemNumber())
                            }
                        )
                        if discount_line_id:
                            discount_line_id.discounting()


class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']
    

    def getAmountDiscount_t2_47(self):
        parent_move_id = self.move_id.reversed_entry_id
        amount = parent_move_id.getAmountLineDiscountItem(self.getItemNumber()) #.getAmountProrated() - self.getAmountDiscount()
        #raise UserError(amount)
        return amount
    
    def getSubTotal_t2_47(self, decimal = 2):
        amount = round( (self.quantity * self.getPriceUnit() ) - self.getAmountDiscount_t2_47() , decimal)
        return  amount
    