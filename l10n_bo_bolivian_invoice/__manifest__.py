# -*- coding: utf-8 -*-

{
    'name': 'Facturación boliviana.',
    'version': '17.0',
    'author' : 'Acoim Ltda.',
    'summary': '(1) (24) (47) Facturacion electronica / computarizada',
    'description': """
        Facturacion boliviana electronica / computarizada
    """,
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_bo', 
        'base_address_extended',
        'l10n_bo_base',
    ],
    'category': 'Accounting',
    'demo': [],
    
    'external_dependencies': {
        'python': [
            'signxml', # => v2.10.1
            'qrcode',
            'lxml',
            'pyOpenSSL', # => v21.0.0
            'cryptography' #=> v3.4.8
        ]
    },
    'data': [
        
        # SECURITY
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        #DATA
        'data/l10n_bo_wsdl_service.xml',
        'data/l10n_bo_catalog.xml',
        'data/res.country.state.csv',
        'data/res.city.csv',
        'data/res.municipality.csv',
        
        #REPORTS
        'reports/paper_formats.xml',
        'reports/layout.xml',
        'reports/purchase_sale.xml',
        #'reports/comercial_export.xml',
        'reports/purchase_sale_roll.xml',
        'reports/credit_debit_note.xml',
        'reports/credit_debit_note_discount.xml',
        'reports/credit_debit_note_ice.xml',
        'reports/ir_actions_report.xml',
        
        

        #TEMPLATES
        'templates/mail_templates.xml',
        'templates/ir_cron.xml',
        

        #SEQUENCES


        #VIEWS
        'views/l10n_bo_wsdl_service.xml',
        'views/l10n_bo_wsdl_operation_service.xml',
        'views/res_company.xml',
        'views/l10n_bo_certificate.xml',
        'views/l10n_bo_branch_office.xml',
        'views/l10n_bo_pos.xml',
        'views/account_journal.xml',
        'views/account_move_base.xml',
        'views/l10n_bo_catalog.xml',
        'views/uom_uom.xml',
        'views/product_template.xml',
        'views/res_currency.xml',
        'views/res_partner.xml',
        'views/l10n_bo_cancellation_reason.xml',
        'views/l10n_bo_global_discount.xml',
        'views/l10n_bo_line_discount.xml',
        'views/significant_event.xml',
        'views/l10n_bo_cufd.xml',
        'views/l10n_bo_package.xml',
        'views/l10n_bo_cafc.xml',        
        'views/menu.xml',

        # VIEWS WIZARD
        'wizard/l10n_bo_pos_register_wizard.xml',
        'wizard/demo_invoice_line_wizard.xml',
        'wizard/demo_invoice_wizard.xml',
        'wizard/demo_invoice_cancellation_line_wizard.xml',
        'wizard/demo_invoice_reversion_line_wizard.xml',
        'wizard/demo_invoice_package_line_wizard.xml',
        
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'pre_init_hook': '',
    'assets': {},
    'license': 'OPL-1',
    'website': 'https://www.acoim.com/',
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
