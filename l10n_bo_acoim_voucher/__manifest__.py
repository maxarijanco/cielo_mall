# -*- coding: utf-8 -*-

{
    'name': 'Acoim comprobante (BO).',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': 'Impresion de comprobante contable',
    'depends': [
        'base',
        'account',
        'l10n_bo', 
    ],
    'category': 'Accounting',
    'data': [
        'report/paper_format.xml',
        'report/layout.xml',
        'report/voucher_format.xml',
        'report/ir_actions_report.xml',
    ],
    'external_dependencies': {
        'python': [
            'num2words',
        ]
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores']
}
