{
    "name": "Descuento fijo en facturas",
    "summary": "Permite aplicar descuento fijo en facturas.",
    "version": "17.0",
    "category": "Accounting & Finance",
    'website': 'https://www.acoim.com/',
    'author' : 'Acoim Ltda.',
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["account"],
    "data": [
        "views/account_move_view.xml",
        "reports/report_account_invoice.xml",
        "data/decimal_precision.xml"
    ],
    'maintainer': 'Luis Fernando Hinojosa Flores',
    'contributors': ['Luis Fernando Hinojosa Flores <hinojosafloresluisfernando@gmail.com>']
}
