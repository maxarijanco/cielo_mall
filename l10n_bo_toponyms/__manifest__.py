# -*- coding: utf-8 -*-

{
    'name': 'Topónimos base (BO)',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Departamentos, cuidades, municipios y provincias',
    'depends': [ 
        'base',
        'base_address_extended'
    ],
    'data' : [
        'security/ir.model.access.csv'
    ],
    'category': 'Accounting',
    'installable': True,
    'application': False,
    'auto_install': False,
    'pre_init_hook': '',
    'post_init_hook': '_post_init',
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
