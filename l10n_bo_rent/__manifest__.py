# -*- coding: utf-8 -*-

{
    'name': 'Facturacion alquiler.',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Alquiler de bienes inmuebles propios.',
    'description': """
        Habilitada para alquiler de bienes inmuebles propios.
    """,
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_bo', 
        'base_address_extended',
        'l10n_bo_bolivian_invoice'
    ],
    'category': 'Accounting',
    'data': [
        'views/account_move.xml',
        'report/base.xml',
        'report/letter_size.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
