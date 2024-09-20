# -*- coding: utf-8 -*-
{
    'name': "Notifications on Odometer",

    'summary': """
        Este modulo envia notificacion al encargado al momento en que el odometro supera la cantidad asignada""",

    'description': """
        Este modulo envia notificacion al encargado al momento en que el odometro supera la cantidad asignada
    """,

    'author': "OutsourceArg",
    'website': "https://www.outsourcearg.com",
    'installable':True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['fleet'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
}