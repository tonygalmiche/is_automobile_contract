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
    
    def get_working_day(self, cr, uid, date, num_day, jours_fermes, leave_dates, context=None):
        if int(num_day) not in jours_fermes and date not in leave_dates:
            print 'yesssssss'
            return date
        else:
            date = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)
            date = date.strftime('%Y-%m-%d')
            num_day = time.strftime('%w', time.strptime(date, '%Y-%m-%d'))
            return self.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)            

    def _compute_date_expedition(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            if order.date_livraison:
                # jours de fermeture de la société
                jours_fermes = self.num_closing_days(cr, uid, order.company_id.partner_id, context=context)
                # Jours de congé de la société
                leave_dates = self.get_leave_dates(cr, uid, order.company_id.partner_id, context=context)
                
                delai_transport = order.partner_id.delai_transport
                if delai_transport:
                    date = datetime.datetime.strptime(order.date_livraison, '%Y-%m-%d') - datetime.timedelta(days=delai_transport)
                    date = date.strftime('%Y-%m-%d')
                    num_day = time.strftime('%w', time.strptime(date, '%Y-%m-%d'))
                    date_expedition = self.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)         
                    res[order.id] = date_expedition
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

    def onchange_date_livraison(self, cr, uid, ids, date_livraison, partner_id, company_id, context=None):
        v = {}
        warning = {}
        
        if partner_id and date_livraison:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            
            # jours de fermeture de la société
            jours_fermes = self.num_closing_days(cr, uid, company.partner_id, context=context)
            print 'jours_femers******', jours_fermes
            # Jours de congé de la société
            leave_dates = self.get_leave_dates(cr, uid, company.partner_id, context=context)
            print 'leave dates*******',  leave_dates  
            delai_transport = partner.delai_transport
            if delai_transport:
                date = datetime.datetime.strptime(date_livraison, '%Y-%m-%d') - datetime.timedelta(days=delai_transport)
                date = date.strftime('%Y-%m-%d')
                print 'date*****', date
                num_day = time.strftime('%w', time.strptime(date, '%Y-%m-%d'))
                print 'num day ******', num_day
                date_expedition = self.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)         
                v['date_expedition'] = date_expedition
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
