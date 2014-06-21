# -*- coding: utf-8 -*-

import time
import datetime

from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _compute_date_expedition(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            if order.date_livraison:           
                num_day = time.strftime('%w', time.strptime(order.date_livraison, '%Y-%m-%d'))

                delai_transport = order.partner_id.delai_transport
                if delai_transport:
                    if int(num_day) <= delai_transport:
                        delai_transport += 2
                    date = datetime.datetime.strptime(order.date_livraison, '%Y-%m-%d') - datetime.timedelta(days=delai_transport)
                    res[order.id] = date.strftime('%Y-%m-%d')
                else:
                    res[order.id] = order.date_livraison
        return res

    _columns = {
        'type_contrat': fields.selection([('ferme', 'Ferme'),('previsionnel', 'Previsionnel')], "Type"),
        'date_livraison': fields.date("Date de livraison"),
        'date_expedition': fields.function(_compute_date_expedition, type="date", string="Date d'expedition", readonly=True, store=True),
        'contract_id': fields.many2one('contract.automobile', 'Contrat'),
    }

    def onchange_date_livraison(self, cr, uid, ids, date_livraison, partner_id, context=None):
        v = {}

        if date_livraison:           
            num_day = time.strftime('%w', time.strptime(date_livraison, '%Y-%m-%d'))

            delai_transport = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).delai_transport
            if delai_transport:
                if int(num_day) <= delai_transport:
                    delai_transport += 2
                date = datetime.datetime.strptime(date_livraison, '%Y-%m-%d') - datetime.timedelta(days=delai_transport)
                v['date_expedition'] = date.strftime('%Y-%m-%d')
            else:
                v['date_expedition'] = date_livraison
        return {'value': v}

sale_order()
