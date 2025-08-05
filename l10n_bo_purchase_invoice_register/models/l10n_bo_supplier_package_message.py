# -*- coding:utf-8 -*-

from odoo import api, models, fields

class L10nBoSupplierPackageMessage(models.Model):
    _name = 'l10n.bo.supplier.package.message'
    _description = 'Lita de mensajes de paquetes de proveedores'

    
    name = fields.Datetime(
        string='Fecha hora',
        default=fields.Datetime.now,
    )

    
    code = fields.Integer(
        string='Codigo',
    )

    
    description = fields.Char(
        string='Descripcion',
    )


    
    supplier_package_id = fields.Many2one(
        string='Paquete de proveeedor',
        comodel_name="l10n.bo.supplier.package",
    )
    