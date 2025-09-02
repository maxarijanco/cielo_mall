# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = ['account.move']

    
    from_period = fields.Date(
        string='Del',
        copy=False,
        help='Usado para el periodo de la facuturación de alquiler'
    )

    
    to_period = fields.Date(
        string='Al',
        copy=False,
        help='Usado para el periodo de la facuturación de alquiler'
    )
    
    
    
    

    
    
    def rent_format(self):
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
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial(to_xml=True)}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.partner_id.getNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.partner_id.getComplement()}</complemento>""" if self.partner_id.complement else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""
        cabecera += f"""<periodoFacturado>{self.getPeriod()}</periodoFacturado>"""
        cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
        cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
        cabecera += f"""<montoTotal>{self.getAmountTotal2(2)}</montoTotal>"""
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva2()}</montoTotalSujetoIva>"""
        cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
        cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
        cabecera += f"""<montoTotalMoneda>{self.amountCurrency2()}</montoTotalMoneda>"""
        cabecera += f"""<descuentoAdicional>{self.getAmountDiscount()}</descuentoAdicional>""" if self.amount_discount > 0 else """<descuentoAdicional xsi:nil="true"/>"""
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
                detalle += f"""<codigoProducto>{line.product_id.getCode()}</codigoProducto>"""
                detalle += f"""<descripcion>{line.getDescription(to_xml =True)}</descripcion>"""
                detalle += f"""<cantidad>{round(line.quantity,2)}</cantidad>"""
                detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
                detalle += f"""<precioUnitario>{line.getPriceUnit2()}</precioUnitario>"""
                detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
                detalle += f"""<subTotal>{line.getSubTotal2()}</subTotal>"""
                detalle += """</detalle>"""
        return cabecera + detalle    

    def rent_format_computerized(self):
        rent_format = f"""<facturaComputarizadaAlquilerBienInmueble xsi:noNamespaceSchemaLocation="facturaComputarizadaAlquilerBienInmueble.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        rent_format += self.rent_format()
        rent_format += f"""</facturaComputarizadaAlquilerBienInmueble>"""
        return rent_format
    

    def rent_format_electronic(self):
        rent_format = f"""<facturaElectronicaAlquilerBienInmueble xsi:noNamespaceSchemaLocation="facturaElectronicaAlquilerBienInmueble.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        rent_format += self.rent_format()
        rent_format += f"""</facturaElectronicaAlquilerBienInmueble>"""
        return rent_format

    def getPeriod(self):
        if self.from_period and self.to_period:
            return f"Del {self.from_period.day}/{self.from_period.month}/{self.from_period.year} al {self.to_period.day}/{self.to_period.month}/{self.to_period.year}"
        raise UserError('Nesecita establecer el periodo completo')
    
    def generate_computerized_format_str(self):
        if self.document_type_id:
            if self.document_type_id.getCode() == 2:
                return self.rent_format_computerized()
        return super(AccountMove, self).generate_computerized_format_str()
        
    def generate_electronic_format_srt(self):
        if self.document_type_id:
            if self.document_type_id.getCode() == 2:
                return self.rent_format_electronic()
        return super(AccountMove, self).generate_electronic_format_srt()
        

    def getAvailableDocument(self):
        res : list = super(AccountMove, self).getAvailableDocument()
        return res + [2]
    

    def getAmountTotal2(self, decimal = 2):
        amount = 0
        for line in self.invoice_line_ids:
            if line.display_type == 'product' and not line.product_id.gif_product:
                amount += line.getSubTotal2()
        amount -= self.getAmountDiscount()
        return self.roundingUp(amount, decimal) 
    

    def getAmountOnIva2(self) -> float:
        amount = round(self.getAmountTotal2() - self.getAmountGiftCard(),2)
        return amount
    
    def amountCurrency2(self):
        amount_total = self.getAmountTotal2() / self.currency_id.getExchangeRate() #self.tax_totals.get('amount_total', 0.00)# / self.currency_id.getExchangeRate()
        return round(amount_total, 2) #round(amount_total - self.amount_giftcard,2)