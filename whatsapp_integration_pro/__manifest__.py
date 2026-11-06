# -*- coding: utf-8 -*-
{
    'name': 'WhatsApp Order & Shipping Pro',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Send Sale Orders, Quotations and Delivery Tracking Links via WhatsApp with One Click.',
    'description': 'Professional WhatsApp integration for Sales and Inventory/Delivery.',
    'author': 'Alihan Pehlivan',
    'depends': [
        'sale_management',
        'stock',
        'delivery',
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'price': 39.99,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': False,
}
