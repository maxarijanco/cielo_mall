# -*- coding: utf-8 -*-

from odoo import api, models, fields
import html
class ResPartner(models.Model):
    _inherit = ['res.partner']
    

    
    complement = fields.Char(
        string='Complemento',
        copy=False
    )

    reazon_social = fields.Char(
        string='Razón social',
        copy=False
    )

    code = fields.Char(
        string='Código',
        copy=False,
        help='Código de cliente'
    )



    def getNameReazonSocial(self):
        return self.reazon_social or self.name
        # if to_xml:
        #     return html.escape(nombreRazonSocial) #nombreRazonSocial.replace('&','&amp;')
        # return nombreRazonSocial
    


    def getComplement(self):
        return self.complement
        
    def getNit(self):
        return self.vat
    
    def getCode(self):
        return self.code or self.getNit()