# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Asma BOUSSELMI - CONSULTANT OPENERP CONFIRME
#
##############################################################################

{
    'name': 'Gestion des contrats',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
Gestion des contrats pour le secteur automobile
    """,
    'author': 'Asma BOUSSELMI',
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
