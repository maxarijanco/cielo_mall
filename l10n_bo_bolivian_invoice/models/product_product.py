from odoo import api, models
from odoo.exceptions import UserError
import html
import logging
_logger = logging.getLogger(__name__)



class ProductProduct(models.Model):
    _inherit = ['product.product']

    @api.model
    def getProduct(self):
        return self.env['product.product'].sudo().with_company(self.env.company.getGrandParent().id).browse(self.id)

    def getAe(self):
        if self.siat_service_id:
            return self.siat_service_id.getAe()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getAe()
        raise UserError(f'No se configuro un codigo SIAT para el producto: {self.name}')
        
    
    def getCode(self, to_xml = False):
        if self.default_code:
            return html.escape(self.default_code) if to_xml else self.default_code
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getCode(to_xml)
        raise UserError(f'El producto {self.name} no tiene una referencia interna')
    
    def getServiceCode(self):
        if self.siat_service_id:
            return self.siat_service_id.getCode()
        if not self.company_id and self.env.company.id != self.env.company.getGrandParent().id:
            return self.getProduct().getServiceCode()
        raise UserError(f'El producto {self.name} no tiene un Codigo SIAT.')