{
    'name': 'Broken Loyalty',
    'version': '11.0.1.0.0',
    'depends': ['base'],
    'data': [
        'views/loyalty_card_views.xml',
        'security/ir.model.access.csv',
        'data/loyalty_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'broken_loyalty/static/src/js/loyalty.js',
        ],
    },
    'application': True,
}
