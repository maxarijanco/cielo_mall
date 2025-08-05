# -*- coding: utf-8 -*-

{
    'name': 'Registro de compras (BO).',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Compras (BO)',
    'description': """
        Registro de compras al SIN
    """,
    'depends': ['account'],
    'category': 'Accounting',
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'data/account_tax_group.xml',
        'data/l10n_bo_purchase_register.xml',
        
        'views/account_journal.xml',
        'views/account_tax_group.xml',
        'views/account_move.xml',
        'views/l10n_bo_purchase_register.xml',
        'views/l10n_bo_purchase_register_line.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': '',
    'assets': {},
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores']
}