from odoo import api, models, fields
from odoo.exceptions import UserError
import pytz

from xml.sax.saxutils import escape
import html

class AccountMoveParams(models.Model):
    _inherit = ['account.move']

    def purchase_sale_format(self):
        cabecera = """<cabecera>"""
        cabecera += f"""<nitEmisor>{self.company_id.getNit()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getCompanyName(to_xml=True)}</razonSocialEmisor>"""
        cabecera += f"""<municipio>{self.getMunicipality()}</municipio>"""
        cabecera += f"""<telefono>{self.getPhone()}</telefono>"""
        cabecera += f"""<numeroFactura>{self.getInvoiceNumber()}</numeroFactura>"""
        cabecera += f"""<cuf>{self.getCuf()}</cuf>"""
        cabecera += f"""<cufd>{self.getCufd()}</cufd>"""
        cabecera += f"""<codigoSucursal>{self.getBranchCode()}</codigoSucursal>"""
        cabecera += f"""<direccion>{self.getAddress(to_xml=True)}</direccion>"""
        cabecera += f"""<codigoPuntoVenta>{self.getPosCode()}</codigoPuntoVenta>"""
        cabecera += f"""<fechaEmision>{self.getEmisionDate()}</fechaEmision>"""
        cabecera += f"""<nombreRazonSocial>{self.getNameReazonSocial(to_xml=True)}</nombreRazonSocial>"""
        cabecera += f"""<codigoTipoDocumentoIdentidad>{self.partner_id.getIdentificationCode()}</codigoTipoDocumentoIdentidad>"""
        cabecera += f"""<numeroDocumento>{self.getPartnerNit()}</numeroDocumento>"""
        cabecera += f"""<complemento>{self.getPartnerComplement()}</complemento>""" if self.getPartnerComplement() else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""
        cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
        cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
        cabecera += f"""<montoTotal>{self.getAmountTotal()}</montoTotal>"""
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva()}</montoTotalSujetoIva>"""
        cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
        cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
        cabecera += f"""<montoTotalMoneda>{self.amountCurrency()}</montoTotalMoneda>"""
        cabecera += f"""<montoGiftCard>{self.getAmountGiftCard()}</montoGiftCard>""" if self.is_gift_card and self.amount_giftcard > 0 else """<montoGiftCard xsi:nil="true"/>"""
        cabecera += f"""<descuentoAdicional>{self.getAmountDiscount()}</descuentoAdicional>""" if self.amount_discount > 0 else """<descuentoAdicional xsi:nil="true"/>"""
        cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        cabecera += f"""<cafc>{self.getCafc()}</cafc>""" if self.getCafc() else """<cafc xsi:nil="true"/>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        cabecera += f"""<codigoDocumentoSector>{self.getDocumentSector()}</codigoDocumentoSector>"""
        cabecera += """</cabecera>"""
        
        detalle  = """"""
        for line in self.get_invoice_lines():
            detalle  += """<detalle>"""
            detalle += f"""<actividadEconomica>{line.product_id.getAe()}</actividadEconomica>"""
            detalle += f"""<codigoProductoSin>{line.product_id.getServiceCode()}</codigoProductoSin>"""
            detalle += f"""<codigoProducto>{line.product_id.getCode(to_xml =True)}</codigoProducto>"""
            detalle += f"""<descripcion>{line.getDescription(to_xml =True)}</descripcion>"""
            detalle += f"""<cantidad>{line.getQuantity()}</cantidad>"""
            detalle += f"""<unidadMedida>{line.product_uom_id.getCode()}</unidadMedida>"""
            detalle += f"""<precioUnitario>{line.getPriceUnit()}</precioUnitario>"""
            detalle += f"""<montoDescuento>{line.getAmountDiscount()}</montoDescuento>""" if line.getAmountDiscount() > 0 else """<montoDescuento xsi:nil="true"/>"""
            detalle += f"""<subTotal>{line.getSubTotal()}</subTotal>"""
            detalle += f"""<numeroSerie xsi:nil="true"/>"""
            detalle += f"""<numeroImei xsi:nil="true"/>"""
            detalle += """</detalle>"""
            
        return cabecera + detalle
    
    def purchase_sale_format_computerized(self):
        _format = ''
        #_format = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""
        _format += """<facturaComputarizadaCompraVenta xsi:noNamespaceSchemaLocation="facturaComputarizadaCompraVenta.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        _format += self.purchase_sale_format()
        _format += f"""</facturaComputarizadaCompraVenta>"""
        return _format
    

    def purchase_sale_format_electronic(self):
        #_format = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""
        _format = """<facturaElectronicaCompraVenta xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="facturaElectronicaCompraVenta.xsd">"""
        _format += self.purchase_sale_format()
        _format += f"""</facturaElectronicaCompraVenta>"""
        return _format
    
    # def getNameReazonSocial(self, to_xml = False):
    #     return self.partner_id.getNameReazonSocial(to_xml)


    def getCafc(self):
        cafc = False
        if self.manual_invoice:
            self.write({'cafc' : self.get_cafc_id(get_code = True)})
            cafc = self.cafc
        return  cafc  
    
    # def getPartnerNit(self):
    #     return self.partner_id.getNit()
    
    def getPartnerComplement(self):
        if self.identification_code == 1:
            return self.complement or self.partner_id.getComplement()
        return False
    
    def getPartnerCode(self):
        if self.partner_id.code: return self.partner_id.code
        return self.getPartnerNit()
    
    def getDocumentSector(self):
        if self.document_type_id.name.sector_document_id:
            return self.document_type_id.name.sector_document_id.getCode()
        raise UserError('No tiene un Documento sector')
    
    def getLegend(self):
        if self.legend_id:
            return self.legend_id.descripcionLeyenda
        raise UserError('No tiene una leyenda para la factura')
    
    def getCuf(self):
        if self.cuf:
            return self.cuf
        raise UserError('la factura no tiene generado un cuf')
    
    def getMunicipality(self):
        return self.branch_office_id.getMunicipalityName()
    
    def getPhone(self):
        return self.branch_office_id.getPhone()
    
    # def getCompanyName(self, to_xml = False):
    #     return escape(self.company_id.name) if to_xml else self.company_id.name
    
    def getCufd(self):
        return self.pos_id.getCufd(actual = True)
    
    def getBranchCode(self):
        return self.pos_id.branch_office_id.getCode()
    
    def getAddress(self, to_xml = False):
        return escape(self.pos_id.getAddress()) if to_xml else self.pos_id.getAddress()
    
    def getPosCode(self):
        return self.pos_id.getCode()
    
    def getEmisionDate(self):
        fecha_hora_bolivia = self.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz'))
        return  fecha_hora_bolivia.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
    
    def getPaymentType(self):
        if self.payment_type_id:
            return self.payment_type_id.getCode()
        raise UserError('No tiene un tipo de pago')
    
    def getCard(self):
        if self.card:
            return self.card[:4]+'00000000'+self.card[-4:]
        raise UserError('No se encontro una tarjeta')