# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools import (is_html_empty)
import os
import logging


class AccountMove(models.Model):
    _inherit = ['account.move']
    
    def getAvailableDocument(self):
        res : list = super(AccountMove, self).getAvailableDocument()
        return res + [23]        

    def generate_electronic_format_srt(self):
        if self.document_type_id:
            if self.document_type_id.getCode() == 23:
                return self.prevalued_electronic()
        return super(AccountMove, self).generate_electronic_format_srt()
    

    def generate_computerized_format_str(self):
        if self.document_type_id:
            if self.document_type_id.getCode() == 23:
                return self.prevalued_computerized()
        return super(AccountMove, self).generate_computerized_format_str()
    
    def getAmountTotal(self):
        amount_total = super(AccountMove, self).getAmountTotal()
        return amount_total

    def get_xsd_path(self):
        xsd_name = None
        provider_modality = self.company_id.getL10nBoCodeModality()
        if self.document_type_id:
            if provider_modality == '1' and self.document_type_id.getCode() == 23:
                    pass   
            elif provider_modality == '2' and self.document_type_id.getCode() == 23:
                    xsd_name = 'facturaComputarizadaPrevalorada.xsd'
        if xsd_name:
            return os.path.join(os.path.dirname(__file__), f'../templates/{xsd_name}')
        return super(AccountMove, self).get_xsd_path()
    
    def getNameReazonSocial(self, to_xml = False):
        if self.document_type_id.getCode() == 23:
            return 'S/N'
        return super(AccountMove, self).getNameReazonSocial(to_xml)
    
    def getPartnerNit(self):
        if self.document_type_id.getCode() == 23:
            return 0
        return super(AccountMove, self).getPartnerNit()
    
    def getPartnerCode(self):
        if self.document_type_id.getCode() == 23:
            return 'N/A'
        return super(AccountMove, self).getPartnerCode()
    

        
    
    
    def prevalued_invoice_format(self):
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
        # cabecera += f"""<complemento>{self.getPartnerComplement()}</complemento>""" if self.getPartnerComplement() else """<complemento xsi:nil="true"/>"""
        cabecera += f"""<codigoCliente>{self.getPartnerCode()}</codigoCliente>"""
        cabecera += f"""<codigoMetodoPago>{self.getPaymentType()}</codigoMetodoPago>"""
        cabecera += f"""<numeroTarjeta>{self.getCard()}</numeroTarjeta>""" if self.is_card else """<numeroTarjeta xsi:nil="true"/>"""
        cabecera += f"""<montoTotal>{self.getAmountTotal()}</montoTotal>"""
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIva()}</montoTotalSujetoIva>"""
        cabecera += f"""<codigoMoneda>{self.currency_id.getCode()}</codigoMoneda>"""
        cabecera += f"""<tipoCambio>{self.currency_id.getExchangeRate()}</tipoCambio>"""
        cabecera += f"""<montoTotalMoneda>{self.amountCurrency()}</montoTotalMoneda>"""
        cabecera += f"""<leyenda>{self.getLegend()}</leyenda>"""
        cabecera += f"""<usuario>{self.user_id.name}</usuario>"""
        # cabecera += f"""<montoGiftCard>{self.getAmountGiftCard()}</montoGiftCard>""" if self.is_gift_card and self.amount_giftcard > 0 else """<montoGiftCard xsi:nil="true"/>"""
        # cabecera += f"""<descuentoAdicional>{self.getAmountDiscount()}</descuentoAdicional>""" if self.amount_discount > 0 else """<descuentoAdicional xsi:nil="true"/>"""
        # cabecera += f"""<codigoExcepcion>{1 if self.force_send else 0}</codigoExcepcion>"""
        # cabecera += f"""<cafc>{self.getCafc()}</cafc>""" if self.getCafc() else """<cafc xsi:nil="true"/>"""
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
            detalle += """</detalle>"""
            
        return cabecera + detalle

    def prevalued_computerized(self):
        commercial_export_format = f"""<facturaComputarizadaPrevalorada xsi:noNamespaceSchemaLocation="facturaComputarizadaPrevalorada.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
        commercial_export_format += self.prevalued_invoice_format()
        commercial_export_format += f"""</facturaComputarizadaPrevalorada>"""
        return commercial_export_format
    
    def prevalued_electronic(self):
        commercial_export_format = f"""<facturaElectronicaPrevalorada xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="facturaElectronicaPrevalorada.xsd">"""
        commercial_export_format += self.prevalued_invoice_format()
        commercial_export_format += f"""</facturaElectronicaPrevalorada>"""
        return commercial_export_format