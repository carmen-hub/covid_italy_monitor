{
    'name': 'Covid Italy Monitor',
    'version': '18.0.1.0.0',
    'category': 'Reporting',
    'summary': 'Aggregated COVID-19 cases by Italian region',
    'author': 'Your Name',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/covid_province_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}