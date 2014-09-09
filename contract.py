# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _

class contract_automobile(osv.osv):
    _name = "contract.automobile"
    _description = "Contrats de secteur automobile"
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Client', required=True),
        'product_id': fields.many2one('product.product', 'Produit', required=True),
        'ref_partner': fields.char('Reference Client', size=64),
        'ref_product': fields.char('Reference Produit', size=64, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _sql_constraints = [
        ('ref_client_product_uniq', 'unique (partner_id, ref_partner, ref_product, company_id)', 'Ce client possede un contrat avec la meme reference client et produit que le contrat courant, Veuillez corriger votre saisie !')
    ]

    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'contract.automobile', context=c),
    }
   

contract_automobile()
    
