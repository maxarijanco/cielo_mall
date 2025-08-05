# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

import pytz
import io
import tarfile
import base64
import gzip
import hashlib
import logging
_logger = logging.getLogger(__name__)



class L10nBoSupplierPackageLine(models.Model):
    _name ="l10n.bo.supplier.package.line"
    _description ="Linea de paquete de proveedor (BO)"

    
    name = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        domain=[
            ('move_type','=','in_invoice'),
            ('bo_purchase_edi','=',True),
        ]
    )
    
    
    

    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )
    
    

    
    
    supplier_package_id = fields.Many2one(
        string='Paquete.',
        comodel_name='l10n.bo.supplier.package',
    )