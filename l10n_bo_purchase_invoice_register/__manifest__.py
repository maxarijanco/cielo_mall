# -*- coding: utf-8 -*-

{
    'name': 'Facturación boliviana compras.',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Facturacion compras (BO)',
    'description': """
        Registro de compras al SIN
    """,
    'depends': ['account', 'l10n_bo_purchase_invoice', 'l10n_bo_bolivian_invoice'],
    'category': 'Accounting',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        # 'security/security.xml',
        
        'data/l10n_bo_wsdl_service.xml',
        # 'data/account_tax_group.xml',
        # 'data/l10n_bo_purchase_register.xml',
        
        'template/ir_sequence.xml',
        'views/account_move.xml',
        'views/l10n_bo_supplier_package_line.xml',
        'views/l10n_bo_supplier_package_message.xml',
        'views/l10n_bo_supplier_package.xml',
        
        'views/menuitem.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': '',
    'post_init_hook': '_post_init',
    
    'assets': {},
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
