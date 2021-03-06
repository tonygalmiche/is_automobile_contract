# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Asma BOUSSELMI - CONSULTANT OPENERP CONFIRME
#
##############################################################################

import time
import datetime

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class contract_line(osv.osv_memory):
    _name = "contract.line"
    _description = "Lines of contract"
    _columns = {
        'date_livraison': fields.date('Date Livraison', required=True),
        'date_expedition': fields.date('Date Expedition', required=True),
        'type': fields.selection([('ferme','Ferme'),('previsionnel','Previsionnel')], 'Type', required=True),
        'contract_id': fields.many2one('contract.quotations', 'Reference contrat', required=True, ondelete='cascade', select=True, readonly=True),
        'quantity': fields.float('Quantite'),
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
    
    def onchange_date_livraison(self, cr, uid, ids, date_livraison, delai_transport, partner_id, company_id, context=None):
        v = {}
        warning = {}
        if partner_id and date_livraison:
            is_api = self.pool.get('is.api')
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            
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
                    date_expedition = is_api.get_working_day(cr, uid, date, num_day, jours_fermes, leave_dates, context=context)         
                    i += 1
                
            v['date_expedition'] = date_expedition
        
            check_date = self.check_date_livraison(cr, uid, ids, date_livraison, partner_id, context=context)
            if not check_date:
                warning = {
                            'title': _('Warning!'),
                            'message' : 'La date de livraison tombe pendant la fermeture du client.'
                    }
        
        return {'value': v,
                'warning': warning}
        
        
    def onchange_product_qty(self, cr, uid, ids, product_id, quantity, context=None):
        val = {}
        if product_id and quantity:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context)
            qty = self.pool.get('sale.order.line').calcul_quantity(cr, uid, product, quantity, context)
            print 'qty *****', qty
            val['quantity'] = qty
        return {'value': val}


contract_line()


class contract_generate_quotations(osv.osv_memory):

    _name = "contract.quotations"
    _description = "Generate quotations from contract"
    _columns = {
        'contract_lines': fields.one2many('contract.line', 'contract_id', 'Lignes de contrat', required=True),
        'partner_id': fields.many2one('res.partner', 'Client', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'product_id': fields.many2one('product.product', 'Produit', readonly=True),
        'delai_transport': fields.integer('Delai de transport', readonly=True),
        'affichage': fields.boolean('Afficher tous les devis existants'),
    }

    _defaults = {
        'affichage': True,
    }

    def get_exist_quotations(self, cr, uid, partner_id, product_id, context=None):
        cr.execute("SELECT sale.date_livraison, sale.date_expedition, sale.type_contrat, line.product_uom_qty " \
                   "FROM sale_order sale JOIN sale_order_line line ON sale.id = line.order_id " \
                   "WHERE sale.state = 'draft' and sale.partner_id = %s and line.product_id = %s ", (partner_id, product_id,))
        result = cr.fetchall()
        res = []
        if result:
            for item in result:
                vals = {
                    'date_livraison': item[0] and item[0] or '',
                    'date_expedition': item[1] and item[1] or '',
                    'type': item[2],
                    'quantity': item[3],                  
                }
                res.append(vals)
        return res

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(contract_generate_quotations, self).default_get(cr, uid, fields, context=context)
        contract_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not contract_ids or len(contract_ids) != 1:
            return res
        assert active_model in ('contract.automobile'), 'Bad context propagation'
        contract_id, = contract_ids
        contract = self.pool.get('contract.automobile').browse(cr, uid, contract_id, context=context)
        if 'company_id' in fields:
            res.update(company_id=contract.company_id.id)
        if 'partner_id' in fields:
            res.update(partner_id=contract.partner_id.id)
        if 'product_id' in fields:
            res.update(product_id=contract.product_id.id)
        if 'delai_transport' in fields:            
            res.update(delai_transport=contract.partner_id.delai_transport)
        #chercher les devis du client courant
        if 'contract_lines' in fields:
            lines = self.get_exist_quotations(cr, uid, contract.partner_id.id, contract.product_id.id, context=context)
            res.update(contract_lines=lines)        
        return res

    def onchange_affichage(self, cr, uid, ids, affichage, partner_id, product_id, context=None):
        v = {}
        if affichage:
            v['contract_lines'] = self.get_exist_quotations(cr, uid, partner_id, product_id, context=context)
        else:
            v['contract_lines'] = []
        return {'value': v}
                 

    def generate_quotations(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('contract.automobile')
        contract_line_obj = self.pool.get('contract.line')
        sale_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        result = []
        
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]

        if data:
            for contract in contract_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
                #Supprimer les devis associés à ce contrat
                sale_ids = sale_obj.search(cr, uid, [('contract_id','=',contract.id),('state','=','draft')], context=context)
                sale_obj.unlink(cr, uid, sale_ids, context=None)

                #Generer les nouveaux devis
                for line_id in data['contract_lines']:
                    line = contract_line_obj.browse(cr, uid, line_id, context=context)

                    quotation_line = order_line_obj.product_id_change(cr, uid, ids, contract.pricelist_id.id, contract.product_id.id, 0, False, 0, False, '', contract.partner_id.id, False, True, False, False, False, False, context=context)['value']
                    quotation_line.update({'product_id':contract.product_id.id, 'product_uom_qty': line.quantity})
                    
                    quotation = sale_obj.onchange_partner_id(cr, uid, ids, contract.partner_id.id, context=context)['value']

                    quotation_values = {
                        'name': '/',
                        'partner_id': contract.partner_id.id,
                        'client_order_ref': contract.ref_partner,
                        'contract_id': contract.id,
                        'type_contrat': line.type,
                        'date_livraison': line.date_livraison,
                        'date_expedition': line.date_expedition,
                        'origin': contract.ref_partner and  contract.ref_partner + ', ' + contract.ref_product or contract.ref_product,
                        'order_line': [[0,False,quotation_line]],
                        'picking_policy': 'direct',
                        'order_policy': 'picking',
                        'invoice_quantity': 'order',
                    }

                    quotation.update(quotation_values)
                    res = sale_obj.create(cr, uid, quotation, context=context)
                    result.append(res)

        action_model = False
        data_pool = self.pool.get('ir.model.data')
        action = {}
        action_model,action_id = data_pool.get_object_reference(cr, uid, 'sale', "action_quotations")
        
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in', ["+','.join(map(str,result))+"])]"
        return action
                                        
                
            

        
        
