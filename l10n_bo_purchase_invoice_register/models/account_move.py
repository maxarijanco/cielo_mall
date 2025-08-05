# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import os
import base64
from odoo.exceptions import ValidationError
from lxml import objectify
from lxml import etree

import pytz
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    
    bo_purchase_edi_received = fields.Boolean(
        string='Factura compra validada',
        copy=False
    )        
    
    def edi_purchase_format(self):
        cabecera = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""
        cabecera += """<registroCompra>"""
        cabecera += f"""<nro>{self.get_purchase_sequence()}</nro>"""
        cabecera += f"""<nitEmisor>{self.getEmisorNIT()}</nitEmisor>"""
        cabecera += f"""<razonSocialEmisor>{self.getRazonSocialSupplier(to_xml=True)}</razonSocialEmisor>"""
        cabecera += f"""<codigoAutorizacion>{self.getCufSupplier()}</codigoAutorizacion>"""
        cabecera += f"""<numeroFactura>{self.getInvoiceBillNumber()}</numeroFactura>"""
        cabecera += f"""<numeroDuiDim>{self.getDUIDIMNumber()}</numeroDuiDim>"""
        cabecera += f"""<fechaEmision>{self.getEmisionDate()}</fechaEmision>"""
        cabecera += f"""<montoTotalCompra>{self.getAmountTotalSupplier()}</montoTotalCompra>"""
        cabecera += f"""<importeIce>{self.getAmountIceFromSupplier()}</importeIce>"""
        cabecera += f"""<importeIehd>{self.getAmountIehdFromSupplier()}</importeIehd>"""
        cabecera += f"""<importeIpj>{self.getAmountIpjFromSupplier()}</importeIpj>"""
        cabecera += f"""<tasas>{self.getAmountRateFromSupplier()}</tasas>"""
        cabecera += f"""<otroNoSujetoCredito>{self.getAmountNoIvaFromSupplier()}</otroNoSujetoCredito>"""
        cabecera += f"""<importesExentos>{self.getAmountExemptFromSupplier()}</importesExentos>"""
        cabecera += f"""<importeTasaCero>{self.getAmountZeroRateFromSupplier()}</importeTasaCero>"""
        cabecera += f"""<subTotal>{self.getAmountSubTotalSupplier()}</subTotal>"""
        cabecera += f"""<descuento>{self.getAmountDisccountSupplier()}</descuento>"""
        cabecera += f"""<montoGiftCard>{self.getAmountGifCardSuppllier()}</montoGiftCard>"""
        cabecera += f"""<montoTotalSujetoIva>{self.getAmountOnIvaSupplier()}</montoTotalSujetoIva>"""
        cabecera += f"""<creditoFiscal>{round(self.getAmountOnIvaSupplier() * 0.13, 2)}</creditoFiscal>"""
        cabecera += f"""<tipoCompra>{self.getPurchaseType()}</tipoCompra>"""
        cabecera += f"""<codigoControl>{self.getControlCodeSupplier()}</codigoControl>"""
        cabecera += """</registroCompra>"""
        return cabecera
    

    def _validate_xml(self, xml_str, xsd_path):
        try:
            with open(xsd_path, 'rb') as xsd_file:
                xmlschema_doc = etree.parse(xsd_file)
                xmlschema = etree.XMLSchema(xmlschema_doc)
                
            parser = etree.XMLParser(recover=True)
            xml_doc = etree.fromstring(xml_str.encode('utf-8'), parser)

            if not xmlschema.validate(xml_doc):
                # Obtener los errores de validación
                log = xmlschema.error_log
                error_details = "\n".join([f"Linea {error.line}: {error.message}" for error in log])
                raise ValidationError(f"El XML no es válido según el esquema XSD proporcionado.\nErrores:\n{error_details}")
        except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
            raise ValidationError(f"Error al analizar el XML o el esquema XSD: {str(e)}")
        except IOError as e:
            raise ValidationError(f"No se pudo leer el archivo XSD: {str(e)}")

    
    def validate_edi_purchase_xml(self):
        for record in self:
            if record.edi_str:
                # Ruta absoluta al archivo XSD
                xsd_path = os.path.join(os.path.dirname(__file__), '../data/registroCompra.xsd')
                self._validate_xml(record.edi_str, xsd_path)


    def generate_edi_purchase_xml(self, _ir = False):
        if self.edi_str:
            edi_tree_signed = self.edi_str.encode('utf-8')
            _name_file = f'{self.name} RECEPCION (BO) - XML'

            attacht_id = self.env['ir.attachment'].search(
                [
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('name', '=', _name_file)
                ]
                ,limit=1
            )
            
            if not attacht_id:
                if not _ir:
                    attacht_id = self.env['ir.attachment'].create({
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary',
                        'name': _name_file,
                        'datas': base64.b64encode(edi_tree_signed),
                        'mimetype': 'application/xml'
                    })
                else:
                    raise UserError(f'No se encontro XML de factura de proveedores, {self.name}')
            else:
                if _ir:
                    return attacht_id
                attacht_id.write({'datas': base64.b64encode(edi_tree_signed), 'mimetype': 'application/xml',})
        else:
            _logger.info(f"La factura: {self.name} no genero un XML")
            
    def generate_confirmation_edi_purchase_xml(self, _edi_str = False, _ir = False):
        if self.edi_str:
            if _edi_str:
                edi_tree_signed = _edi_str.encode('utf-8')
            _name_file = f'{self.name} CONFIRMACION (BO) - XML'

            attacht_id = self.env['ir.attachment'].search(
                [
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('name', '=', _name_file)
                ]
                ,limit=1
            )
            
            if not attacht_id:
                if not _ir or _edi_str:
                    attacht_id = self.env['ir.attachment'].create({
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary',
                        'name': _name_file,
                        'datas': base64.b64encode(edi_tree_signed),
                        'mimetype': 'application/xml'
                    })
                else:
                    raise UserError(f'No se encontro XML de factura de proveedores, {self.name}')
            else:
                if _ir:
                    return attacht_id
                if _edi_str:
                    attacht_id.write({'datas': base64.b64encode(edi_tree_signed), 'mimetype': 'application/xml',})
        else:
            _logger.info(f"La factura: {self.name} no genero un XML")
            
        
        
    def generate_edi_purchase_str(self):
        self.write({'edi_str' : self.edi_purchase_format()})
        _logger.info("Formato EDI Purchase")
        _logger.info(f"{self.edi_str}")
    
    def action_purchase_edi(self):
        
        super(AccountMove, self).action_purchase_edi()
        self.generate_edi_purchase_str()
        self.validate_edi_purchase_xml()
        self.generate_edi_purchase_xml()



    
    # @api.constrains('invoice_date_edi')
    # def _check_purchase_invoice_date_edi(self):
    #     for record in self:
    #         if record.bo_purchase_edi and record.move_type in ['in_invoice']:
    #             fechaHora = record.invoice_date_edi.astimezone(pytz.timezone('America/La_Paz'))
    #             record.write({'invoice_date' : fechaHora, 'date': fechaHora})


    

    
    def errorMessague(self):
        for record in self:
            if record.bo_purchase_edi_received:
                raise UserError('Accion no valida para documentos fiscales de compras, esta factura esta procesada por el envio de paquetes (BO) al SIN.')
        
    def button_draft(self):
        self.errorMessague()
        res = super(AccountMove, self).button_draft()
        return res
    
    def confirmation_edi_purchase_format(self):
        cabecera = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""
        cabecera += """<confirmacionCompra>"""
        cabecera += f"""<nro>{self.get_purchase_sequence()}</nro>"""
        cabecera += f"""<nitEmisor>{self.getEmisorNIT()}</nitEmisor>"""
        cabecera += f"""<codigoAutorizacion>{self.getCufSupplier()}</codigoAutorizacion>"""
        cabecera += f"""<numeroFactura>{self.getInvoiceBillNumber()}</numeroFactura>"""
        cabecera += f"""<tipoCompra>{self.getPurchaseType()}</tipoCompra>"""
        cabecera += """</confirmacionCompra>"""
        return cabecera
    
    def validate_confirmation_edi_purchase_xml(self):
        for record in self:
            xsd_path = os.path.join(os.path.dirname(__file__), '../data/confirmacionCompra.xsd')
            record._validate_xml(record.confirmation_edi_purchase_format(), xsd_path)
            record.generate_confirmation_edi_purchase_xml(_edi_str = record.confirmation_edi_purchase_format())