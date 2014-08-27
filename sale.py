# -*- coding: utf-8 -*-

import time
import datetime

from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def num_closing_days(self, cr, uid, partner_id, context=None):
        jours_fermes = []
        if partner_id.close_monday:
            jours_fermes.append(1)
        if partner_id.close_tuesday:
            jours_fermes.append(2)
        if partner_id.close_wednesday:
            jours_fermes.append(3)
        if partner_id.close_thursday:
            jours_fermes.append(4)
        if partner_id.close_friday:
            jours_fermes.append(5)
        if partner_id.close_saturday:
            jours_fermes.append(6)
        if partner_id.close_sunday:
            jours_fermes.append(0)
        return jours_fermes
    
    def get_leave_dates(self, cr, uid, partner_id, context=None):
        leave_dates = []
        if partner_id.calendar_line:
            for line in partner_id.calendar_line:                                                                                                                                                            
                delta = datetime.datetime.strptime(line.date_to, DATETIME_FORMAT) - datetime.datetime.strptime(line.date_from, DATETIME_FORMAT)
                for i in range(delta.days + 1):
                    date = datetime.datetime.strptime(line.date_from, DATETIME_FORMAT) + datetime.timedelta(days=i)
                    leave_dates.append(date.strftime('%Y-%m-%d'))
        return leave_dates
                

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
    
    def check_date_livraison(self, cr, uid, ids, date_livraison,  partner_id, context=None):
        print 'partner_id******', partner_id
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            # jours de fermeture de la société
            jours_fermes = self.num_closing_days(cr, uid, partner, context=context)
            # Jours de congé de la société
            leave_dates = self.get_leave_dates(cr, uid, partner, context=context)
            # num de jour dans la semaine de la date de livraison
            num_day = time.strftime('%w', time.strptime(date_livraison, '%Y-%m-%d'))
            
            if int(num_day) in jours_fermes or date_livraison in leave_dates:
                return False
        return True

    def onchange_date_livraison(self, cr, uid, ids, date_livraison, partner_id, context=None):
        v = {}
        warning = {}
        
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
        
            check_date = self.check_date_livraison(cr, uid, ids, date_livraison, partner_id, context=context)
            if not check_date:
                warning = {
                    'title': _('Warning!'),
                    'message' : 'La date de livraison tombe pendant la fermeture du client.'
                }
        return {'value': v,
                'warning': warning}

sale_order()
