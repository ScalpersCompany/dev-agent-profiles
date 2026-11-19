{
    'name': 'Broken Loyalty',
    'summary': 'Loyalty cards with intentional review defects',
    'version': '11.0.1.0.0',
    'depends': ['base', 'sale'],
    'data': [
        'views/loyalty_card_views.xml',
        'data/loyalty_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'broken_loyalty/static/src/js/loyalty.js',
        ],
    },
    'installable': True,
}
