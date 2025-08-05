# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)



class AccountMove48Params(models.Model):    
    _inherit = ['account.move']
    
    def credit_debit_note_ice_format(self):
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
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial(True)}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.getPartnerNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.getPartnerComplement()}</complemento>""" if self.getPartnerComplement() else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""
        cabecera += f"""<numeroFactura>{self.getOriginalInvoiceNumber()}</numeroFactura>"""
        cabecera += f"""<numeroAutorizacionCuf>{self.getOriginalCuf()}</numeroAutorizacionCuf>"""
        cabecera += f"""<fechaEmisionFactura>{self.getOriginalInvoiceDate()}</fechaEmisionFactura>"""
        cabecera += f"""<montoTotalOriginal>{self.amount_total_original_48(2)}</montoTotalOriginal>"""
        
        cabecera += f"""<descuentoAdicional>{self.reversed_entry_id.getAmountDiscount()}</descuentoAdicional>"""  if self.reversed_entry_id.getAmountDiscount()>0 else """<descuentoAdicional xsi:nil="true"/>"""
        cabecera += f"""<montoTotalDevuelto>{self.amount_returned_48()}</montoTotalDevuelto>"""
        cabecera += f"""<montoDescuentoCreditoDebito>{self.getAmountDiscountCreditDebit_48()}</montoDescuentoCreditoDebito>"""# if self.amount_discount > 0 else """<montoDescuentoCreditoDebito xsi:nil="true"/>"""
        cabecera += f"""<montoEfectivoCreditoDebito>{self.getAmountEffective_48()}</montoEfectivoCreditoDebito>"""
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
                detalle += f"""<montoDescuento>{line.getAmountDiscount_14(5)}</montoDescuento>""" if line.getAmountDiscount_14() > 0 else """<montoDescuento xsi:nil="true"/>"""
                #detalle += f"""<montoDescuento>{line.prorated_line_discount}</montoDescuento>""" if line.prorated_line_discount > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubtotalCalculateIce(5)}</subTotal>"""
                
                
                detalle += f"""<marcaIce>{line.getIceBrand()}</marcaIce>"""
                detalle += f"""<alicuotaIva>{line.getAmountIva_14(5)}</alicuotaIva>"""
                detalle += f"""<precioNetoVentaIce>{line.getAmountIce(5)}</precioNetoVentaIce>"""
                detalle += f"""<alicuotaEspecifica>{line.getSpecificAliquot(decimal=5)}</alicuotaEspecifica>"""
                detalle += f"""<alicuotaPorcentual>{line.getPercentageAliquot()}</alicuotaPorcentual>"""
                detalle += f"""<montoIceEspecifico>{line.getSpecificIce(5)}</montoIceEspecifico>"""
                detalle += f"""<montoIcePorcentual>{line.getPercentageIce(5)}</montoIcePorcentual>"""
                detalle += f"""<cantidadIce>{line.getQuantityIce()}</cantidadIce>""" if line.getQuantityIce() > 0 else """<cantidadIce xsi:nil="true"/>"""
                
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
                detalle += f"""<montoDescuento>{line.getAmountDiscount_t2_48()}</montoDescuento>""" if line.getAmountDiscount_t2_48() > 0 else """<montoDescuento xsi:nil="true"/>"""
                #raise UserError(line.ap())
                detalle += f"""<subTotal>{line.getSubTotal_t2_14(5)}</subTotal>"""
                
                detalle += f"""<marcaIce>{line.getIceBrand()}</marcaIce>"""
                detalle += f"""<alicuotaIva>{line.getAmountIva_14(5)}</alicuotaIva>"""
                detalle += f"""<precioNetoVentaIce>{line.getAmountIce(5)}</precioNetoVentaIce>"""
                detalle += f"""<alicuotaEspecifica>{line.getSpecificAliquot(5)}</alicuotaEspecifica>"""
                detalle += f"""<alicuotaPorcentual>{line.getPercentageAliquot()}</alicuotaPorcentual>"""
                detalle += f"""<montoIceEspecifico>{line.getSpecificIce(5)}</montoIceEspecifico>"""
                detalle += f"""<montoIcePorcentual>{line.getPercentageIce(5)}</montoIcePorcentual>"""
                detalle += f"""<cantidadIce>{line.getQuantityIce()}</cantidadIce>""" if line.getQuantityIce() > 0 else """<cantidadIce xsi:nil="true"/>"""
                
                detalle += f"""<codigoDetalleTransaccion>2</codigoDetalleTransaccion>"""
                
                detalle += """</detalle>"""
        return cabecera + detalle

    def credit_debit_note_ice_format_computerized(self):
        _format = f"""<notaComputarizadaCreditoDebitoIce xsi:noNamespaceSchemaLocation="notaComputarizadaCreditoDebitoIce.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        _format += self.credit_debit_note_ice_format()
        _format += f"""</notaComputarizadaCreditoDebitoIce>"""
        return _format
    

    def credit_debit_note_ice_format_electronic(self):
        _format = f"""<notaElectronicaCreditoDebitoIce xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="/creditoDebito/notaElectronicaCreditoDebitoIce.xsd">"""
        _format += self.credit_debit_note_ice_format()
        _format += f"""</notaElectronicaCreditoDebitoIce>"""
        return _format
    
    def getAmountSubTotal_48(self, decimal = 2):
        if self.tax_totals:
            amount_total = 0
            for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.gif_product:
                    amount_total += line.getSubTotal_48()
            return self.roundingUp(amount_total, decimal)
        return 0
    
    
    

    def getAmountTotal_48(self, decimal = 2):
        if self.tax_totals:
            amount_total = self.getAmountSubTotal_48()
            amount_total -= self.getAmountDiscount()
            #raise UserError()
            return round(amount_total,decimal)
        return 0
    
    
    def amount_returned_48(self):
        amount = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.global_discount:    
                amount += line.getSubTotal_t2_14(5)
        #raise UserError(amount)
        return round(amount, 2) # -  (sum([ self.reversed_entry_id.getAmountProrated(item.item_number)  for item in self.invoice_line_ids ]) / self.getAmountTotal_48())

    def get_apportionment_specific(self, item):
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.global_discount:    
                if line.getItemNumber() == item:
                    return line.apportionment_partial()
        return 0

    def getAmountDiscountCreditDebit_48(self):
        #amount =  self.getAmountTotalProrated(decimal=4)  * self.currency_id.getExchangeRate() #sum([ item.amount_discount  for item in self.invoice_line_ids ])
        amount = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.global_discount:    
                amount += self.reversed_entry_id.get_apportionment_specific(line.getItemNumber()) 
        return round(amount * self.currency_id.getExchangeRate(), 2) # -  (sum([ self.reversed_entry_id.getAmountProrated(item.item_number)  for item in self.invoice_line_ids ]) / self.getAmountTotal_48())

        
        _logger.info(f"Monto total prorrateado  {amount}")
        amount_line_discount = self.getAmountTotalDiscountLine()
        _logger.info(f"Monto total por linea de descuento  {amount_line_discount}")

        amount -= amount_line_discount
        _logger.info(f"Monto total de descuento global prorrateado:  {amount}")
        return round(amount, 2)
    
    def getAmountOnIva_48(self) -> float:
            amount = round(self.getAmountTotal_48() - self.getAmountGiftCard(),2)
            return amount
    
    def getAmountEffective_48(self):
        for record in self:
            return record.roundingUp(record.amount_returned_48() * 0.13, 2)
            return round(record.amount_returned_48() * 0.13, 2)
        

    def amount_total_original_48(self,decimal = None):
        amount = 0
        for line in self.reversed_entry_id.invoice_line_ids:
            amount += line.getSubtotalCalculateIce()
        return self.roundingUp(amount, decimal) if decimal else amount
        

    def getAmountTotalDiscountLine(self):
        amount = 0
        for line in self.invoice_line_ids:
            amount += self.reversed_entry_id.getAmountLineDiscountItem(line.getItemNumber())
        return amount
    
    def _set_default_document_type(self):
        super(AccountMove48Params, self)._set_default_document_type()
        if self.reversed_entry_id and self.reversed_entry_id.document_type_id.getCode() == 14:
            if self.pos_id:
                self.write({'document_type_id' : self.get_credit_debit_ice_id()}) 
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

    
    
    def get_credit_debit_ice_id(self):
        sequence_id = self.pos_id.sequence_ids.filtered(lambda sequence_id:sequence_id.getCode() == 48)[:1]
        return sequence_id[0].id if sequence_id else False
   
    def getSpecificIceTotal(self, decimal = 2):
            amount_total = 0
            for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.gif_product:
                    amount_total += line.getSpecificIce()
            return round(amount_total,decimal)

    def getPercentageIceTotal(self, decimal = 2):
            amount_total = 0
            for line in self.invoice_line_ids:
                if line.display_type == 'product' and not line.product_id.gif_product:
                    amount_total += line.getPercentageIce()

            #raise UserError(amount_total)
            return self.roundingUp(amount_total,decimal)
        
class AccountMoveLine(models.Model):
    
    _inherit = ['account.move.line']
    
    def getAmountDiscount_t2_48(self):
        parent_move_id = self.move_id.reversed_entry_id
        amount = parent_move_id.getAmountLineDiscountItem(self.getItemNumber()) #.getAmountProrated() - self.getAmountDiscount()
        #raise UserError(amount)
        return amount

    
    def getSubTotal_48(self, decimal = 2 ):
        amount = round( (self.quantity * self.getPriceUnit() ) - self.apportionment_partial() , decimal)
        amount += self.getSpecificIce() + self.getPercentageIce()
        #raise UserError(amount)
        return  amount
    
    def getSubTotal_t2_14(self, decimal = None):
        base = self.base_14() # (cantidad * precio)  - descuento
        discount = self.getAmountDiscount_t2_48()
        apportionment_partial = self.move_id.reversed_entry_id.get_apportionment_specific(self.getItemNumber()) #apportionment_partial()
        apportionment_partial *= self.move_id.currency_id.getExchangeRate()
        amount = base - (discount + apportionment_partial)
        return self.roundingUp(amount,decimal) if decimal else amount