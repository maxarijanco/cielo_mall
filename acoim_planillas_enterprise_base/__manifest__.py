# -*- coding: utf-8 -*-

{
    'name': "Acoim Recursos Humanos Base",
    'summary': """
        Recursos Humanos de Bolivia
    """,
    'description': """
        Módulo de Recursos Humanos. Para la versión Odoo 17.enterprise Base
    """,
    'author': "Acoim Ltda.",
    'website': "https://www.acoim.com/",
    'category': 'Acoim',
    'version': '17.0',
    'depends': [
        'hr',
        'hr_payroll',
    ],
    'data': [
        'data/security.xml',
        'data/hr_payroll_data.xml',
        'data/data.xml',
        'views/hr_views.xml',
        'views/hr_payslip_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_view.xml',
        'views/hr_planilla_views.xml',
        'views/hr_planilla_iva_views.xml',
        'views/hr_dias_trabajados_views.xml',
        'views/hr_descuentos_views.xml',
        'views/hr_bonos_views.xml',
        'views/hr_horas_extra_views.xml',
        'security/ir.model.access.csv',
    ],
    'application': False,
}
