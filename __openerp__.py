# -*- coding: utf-8 -*-

{
    'name': 'Gestion des contrats',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
Gestion des contrats pour le secteur automobile
    """,
    'author': 'Tony Galmiche / Asma BOUSSELMI',
    'depends': ['sale'],
    'data': [
        'wizard/generate_quotations_view.xml',
        'contract_view.xml',
        'sale_view.xml',        
        'res_partner_view.xml',
        'wizard/generate_picking_out_view.xml',
        'report/report_quotations_commandes.xml',        
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
