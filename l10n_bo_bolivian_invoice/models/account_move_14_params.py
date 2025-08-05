from odoo import api, models, fields
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


#import pytz


class AccountMove14(models.Model):
    _inherit = ['account.move']

    def ice_format(self):
        cabecera = """<cabecera>"""
        cabecera += f"""<nitEmisor>{self.company_id.getNit()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getCompanyName()}</razonSocialEmisor>"""
        cabecera += f"""<municipio>{self.getMunicipality()}</municipio>"""
        cabecera += f"""<telefono>{self.getPhone()}</telefono>"""
        cabecera += f"""<numeroFactura>{self.getInvoiceNumber()}</numeroFactura>"""
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
        cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
        cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
        cabecera += f"""<montoTotal>{self.amount_total_14(2)}</montoTotal>"""
        cabecera += f"""<montoIceEspecifico>{self.getAmountSpecificIce(2)}</montoIceEspecifico>""" if self.getAmountSpecificIce() > 0 else """<montoIceEspecifico xsi:nil="true"/>"""
        cabecera += f"""<montoIcePorcentual>{self.getAmountPercentageIce(2)}</montoIcePorcentual>""" if self.getAmountPercentageIce() > 0 else """<montoIcePorcentual xsi:nil="true"/>"""
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva_14(2)}</montoTotalSujetoIva>"""
        cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
        cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
        cabecera += f"""<montoTotalMoneda>{self.amountCurrency_14(2)}</montoTotalMoneda>"""
        cabecera += f"""<descuentoAdicional>{self.getAmountDiscount()}</descuentoAdicional>""" if self.getAmountDiscount() != 0 else """<descuentoAdicional xsi:nil="true"/>"""
        cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        cabecera += f"""<cafc>{self.getCafc()}</cafc>""" if self.getCafc() else """<cafc xsi:nil="true"/>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        cabecera += f"""<codigoDocumentoSector>{self.getDocumentSector()}</codigoDocumentoSector>"""
        cabecera += """</cabecera>"""
        
        detalle  = """"""
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                detalle  += """<detalle>"""
                detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
                detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
                detalle += f"""<codigoProducto>{line.product_id.getCode(to_xml =True)}</codigoProducto>"""
                detalle += f"""<descripcion>{line.getDescription(to_xml =True)}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount_14(5)}</montoDescuento>""" if line.getAmountDiscount_14() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubtotalCalculateIce(5)}</subTotal>"""
                detalle += f"""<marcaIce>{line.getIceBrand()}</marcaIce>"""
                detalle += f"""<alicuotaIva>{line.getAmountIva_14(5)}</alicuotaIva>"""
                detalle += f"""<precioNetoVentaIce>{line.getAmountIce(5)}</precioNetoVentaIce>"""
                detalle += f"""<alicuotaEspecifica>{line.getSpecificAliquot(5)}</alicuotaEspecifica>"""
                detalle += f"""<alicuotaPorcentual>{line.getPercentageAliquot()}</alicuotaPorcentual>"""
                detalle += f"""<montoIceEspecifico>{line.getSpecificIce(decimal = 5)}</montoIceEspecifico>"""
                detalle += f"""<montoIcePorcentual>{line.getPercentageIce(5)}</montoIcePorcentual>"""
                detalle += f"""<cantidadIce>{line.getQuantityIce()}</cantidadIce>""" if line.getQuantityIce() > 0 else """<cantidadIce xsi:nil="true"/>"""
                detalle += """</detalle>"""
            
        return cabecera + detalle
    
    def ice_format_computerized(self):
        purchase_sale = f"""<facturaComputarizadaAlcanzadaIce xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="facturaComputarizadaAlcanzadaIce.xsd">"""
        purchase_sale += self.ice_format()
        purchase_sale += f"""</facturaComputarizadaAlcanzadaIce>"""
        return purchase_sale
    

    def ice_format_electronic(self):

        purchase_sale = f"""<facturaElectronicaAlcanzadaIce xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="/alcanzadaIce/facturaElectronicaAlcanzadaIce.xsd">"""
        purchase_sale += self.ice_format()
        purchase_sale += f"""</facturaElectronicaAlcanzadaIce>"""
        return purchase_sale
    
    def getAmountSpecificIce(self, precision = None):
        amount_total = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                amount_total += line.getSpecificIce()        
        return self.roundingUp(amount_total, precision) if precision else amount_total
    
    def getAmountPercentageIce(self, precision = None):
        amount_total = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                amount_total += line.getPercentageIce(precision)
        return self.roundingUp(amount_total, 2) if precision else amount_total
    
    
    def subTotalBase(self):
        amount = 0
        for line in self.invoice_line_ids:
            amount += line.getSubTotal_14()
        _logger.info('Sumatoria totales base')
        _logger.info(amount)
        return amount
    
    def amount_subtotal_14(self, decimal = None):
        amount = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                amount += line.getSubtotalCalculateIce()
        
        _logger.info('Sumatoria subtotales con ice')
        _logger.info(amount)
        return self.roundingUp(amount, decimal) if decimal else amount
    
    def amount_total_14(self, decimal = None):
        amount = self.amount_subtotal_14()
        amount -= self.getAmountDiscount()
        _logger.info('Monto total menos desc Global')
        _logger.info(amount)
        return self.roundingUp(amount, decimal) if decimal else amount
    
    def getAmountOnIva_14(self, decimal = None) -> float:
        #raise UserError(f"{self.amount_total_14(2)} - {self.getAmountSpecificIce(2)} - {self.getAmountPercentageIce(2)}")
        amount = self.amount_total_14(2) - self.getAmountGiftCard()
        amount -= (self.getAmountSpecificIce(2) + self.getAmountPercentageIce(2))
        
        #raise UserError(amount)
        #amount = round(amount - self.getAmountSpecificIce(5) - self.getAmountPercentageIce(), 2)
            #raise UserError(f"ANTES 2 {amount}")
        return self.roundingUp(amount, decimal) if decimal else amount
    
    def amountCurrency_14(self, decimal = None):
        amount_total = self.amount_total_14() / self.currency_id.getExchangeRate() #self.tax_totals.get('amount_total', 0.00)# / self.currency_id.getExchangeRate()
        return self.roundingUp(amount_total,decimal) if decimal else amount_total
