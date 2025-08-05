# -*- coding: utf-8 -*-

{
    'name': "Acoim Recursos Humanos Funcional",
    'summary': """
        Recursos Humanos de Bolivia
    """,
    'description': """
        Módulo de Recursos Humanos. Para la versión Odoo 16.enterprise
    """,
    'author': "Acoim Ltda.",
    'website': "https://www.acoim.com/",
    'category': 'Acoim',
    'version': '17.0',
    'depends': [
        'acoim_planillas_enterprise_base',
    ],
    'data': [
    'report/report_payslip_template.xml',
    'report/report_templates.xml',
    ],

    'application': False,
}
