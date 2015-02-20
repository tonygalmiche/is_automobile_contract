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
                is_api = self.pool.get('is.api')
                # jours de fermeture de la société
                jours_fermes = is_api.num_closing_days(cr, uid, order.company_id.partner_id, context=context)
                # Jours de congé de la société
                leave_dates = is_api.get_leave_dates(cr, uid, order.company_id.partner_id, context=context)
                
                delai_transport = order.partner_id.delai_transport
                if delai_transport:
                    date = datetime.datetime.strptime(order.date_livraison, '%Y-%m-%d') - datetime.timedelta(days=delai_transport)
                    date = date.strftime('%Y-%m-%d')
                    num_day = time.strftime('%w', time.strptime(date, '%Y-%m-%d'))
                    date_expedition = is_api.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)         
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
        is_api = self.pool.get('is.api')
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            # jours de fermeture de la société
            jours_fermes = is_api.num_closing_days(cr, uid, partner, context=context)
            # Jours de congé de la société
            leave_dates = is_api.get_leave_dates(cr, uid, partner, context=context)
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
            is_api = self.pool.get('is.api')
            
            # jours de fermeture de la société
            jours_fermes = is_api.num_closing_days(cr, uid, company.partner_id, context=context)
            # Jours de congé de la société
            leave_dates = is_api.get_leave_dates(cr, uid, company.partner_id, context=context)
            delai_transport = partner.delai_transport
            date_expedition = date_livraison
            if delai_transport:
                i = 0
                while i < delai_transport:
                    date = datetime.datetime.strptime(date_expedition, '%Y-%m-%d') - datetime.timedelta(days=1)
                    date = date.strftime('%Y-%m-%d')
                    num_day = time.strftime('%w', time.strptime(date, '%Y-%m-%d'))
                    date_expedition = is_api.get_day_except_weekend(cr, uid, date, num_day, context=context)         
                    i += 1
                
                date_expedition = is_api.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)
                
            v['date_expedition'] = date_expedition 
        
            check_date = self.check_date_livraison(cr, uid, ids, date_livraison, partner_id, context=context)
            if not check_date:
                warning = {
                            'title': _('Warning!'),
                            'message' : 'La date de livraison tombe pendant la fermeture du client.'
                }
        
        return {'value': v,
                'warning': warning}

sale_order()

class is_sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def calcul_quantity(self, cr, uid, product, quantity, context=None):
        """ Calcul de la quantité d'une ligne de commande en fonction de lot_livraison et multiple_livraison
        """
        if quantity <= product.lot_livraison:
            return product.lot_livraison
        else:
            qty = quantity - product.lot_livraison
            if product.multiple_livraison:
                qty2 = qty / product.multiple_livraison
                if int(qty2) < qty2:
                    qty2 = int(qty2) + 1
                qty = product.lot_livraison + (qty2 * product.multiple_livraison)
            return qty
    
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
         
        res = super(is_sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, 
                                                                update_tax, date_order, packaging, fiscal_position, flag, context)
        """ Arrondir la quantité en fonction de lot de livraison et le multiple de livraison """
        if product :
            if 'product_uom_qty' in res and res['product_uom_qty']:
                qty = res['product_uom_qty']
            prod = self.pool.get('product.product').browse(cr, uid, product, context)
            quantity = self.calcul_quantity(cr, uid, prod, qty, context)
            res['value'].update({'product_uom_qty': quantity})
        return {'value': res['value']}         
            
            
is_sale_order_line()

class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
     
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and context.get('pricelist', False):
            date = context.get('date') or time.strftime('%Y-%m-%d')
            pricelist = self.pool.get('product.pricelist').browse(cr, uid, context.get('pricelist', False), context=context)
            version = False
            for v in pricelist.version_id:
                if ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                    version = v
                    break
            
            if version:
                cr.execute("SELECT distinct(product_id) FROM product_pricelist_item where price_version_id = %s" ,(version.id,))
                ids = [x[0] for x in cr.fetchall()]
                ids = None in ids and  [] or ids
                if ids:
                    args.append(('id', 'in', ids))
                    order = 'default_code'
            else:
                args.append(('id', 'in', []))
            
        return super(product_product, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
 
product_product()   

    
        
