# -*- coding: utf-8 -*-

{
    'name': '(23) Factura prevalorada',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Factura prevalorada',
    'description': """
        Factura prevalorada.
    """,
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_bo',
        'product', 
        'base_address_extended',
        'l10n_bo_bolivian_invoice',
        'l10n_bo_base'
    ],
    'category': 'Accounting',
    'data': [
        
        'reports/base.xml',
        'reports/prevalued.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
