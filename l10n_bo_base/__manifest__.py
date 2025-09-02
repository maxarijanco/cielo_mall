# -*- coding: utf-8 -*-

{
    'name': 'localización base (BO)',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Campos base para la localizacion boliviana',
    'depends': [
        'base',
        'account',
        'l10n_bo', 
        'contacts',
    ],
    'category': 'Accounting',
    'data': [
        'views/account_move.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': '',
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
