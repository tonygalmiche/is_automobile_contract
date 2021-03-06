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

class is_quotation_line(osv.osv_memory):
    _name = "is.quotation.line"
    _description = "Commandes"
    _columns = {
        'date_livraison': fields.date('Date Livraison', required=True),
        'date_expedition': fields.date('Date Expedition', required=True),
        'product_id': fields.many2one('product.product', 'Produit', required=True),
        'picking_id': fields.many2one('is.picking.out', 'Reference', required=True, ondelete='cascade', select=True, readonly=True),
        'quantity': fields.float('Quantite'),
        'sale_id': fields.integer('ID devis', readonly=True)
    }
    
    def onchange_product_qty(self, cr, uid, ids, product_id, quantity, context=None):
        print 'in *****'
        val = {}
        if product_id and quantity:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context)
            qty = self.pool.get('sale.order.line').calcul_quantity(cr, uid, product, quantity, context)
            print 'qty *****', qty
            val['quantity'] = qty
        return {'value': val}

is_quotation_line()


class is_generate_picking_out(osv.osv_memory):

    _name = "is.picking.out"
    _description = "Generate picking out"
    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'partner_id': fields.many2one('res.partner', 'Client', required=True),
        'delivery_date_max': fields.date('Date de livraison maxi', required=True),
        'picking_date': fields.date('Date de bon de livraison', required=True),
        'quotation_lines': fields.one2many('is.quotation.line', 'picking_id', 'Commandes', required=True),
    }
    
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'is.picking.out', context=c),
    }

    def get_quotations(self, cr, uid, partner_id, date_max, context=None):
        cr.execute("SELECT line.product_id, line.product_uom_qty, sale.date_expedition, sale.date_livraison, sale.id " \
                   "FROM sale_order sale JOIN sale_order_line line ON sale.id = line.order_id " \
                   "WHERE sale.state = 'draft' and sale.partner_id = %s and sale.date_livraison <= %s ", (partner_id,date_max,))
        result = cr.fetchall()
        res = []
        if result:
            for item in result:
                vals = {
                    'product_id': item[0],
                    'quantity': item[1],
                    'date_expedition': item[2],
                    'date_livraison': item[3],
                    'sale_id': item[4],
                }
                res.append(vals)
        return res

    def onchange_quotations(self, cr, uid, ids, partner_id, date_max, context=None):
        v = {}
        if partner_id and date_max:
            v['quotation_lines'] = self.get_quotations(cr, uid, partner_id, date_max, context=context)
        else:
            v['quotation_lines'] = []
        return {'value': v}
    

    def generate_picking(self, cr, uid, ids, context=None):
        quotation_obj = self.pool.get('is.picking.out')
        quotation_line_obj = self.pool.get('is.quotation.line')
        stock_obj = self.pool.get('stock.picking')
        sale_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        
        result = []
        
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]

        if data:
            lines = []
            sale_ids = []
            for line in quotation_line_obj.browse(cr, uid, data['quotation_lines'], context=context):
                quotation_line = order_line_obj.product_id_change(cr, uid, ids, 1, line.product_id.id, 0, False, 0, False, '', data['partner_id'][0], False, True, False, False, False, False, context=context)['value']
                quotation_line.update({'product_id':line.product_id.id, 'product_uom_qty': line.quantity})
                lines.append([0,False,quotation_line])
                if not line.sale_id in sale_ids:
                    sale_ids.append(line.sale_id)
                else:
                    continue

            #create quotation
            quotation = sale_obj.onchange_partner_id(cr, uid, ids, data['partner_id'][0], context=context)['value']
            date_expedition = sale_obj.onchange_date_livraison(cr, uid, ids, data['delivery_date_max'], data['partner_id'][0], data['company_id'][0], context=context)['value']['date_expedition']
            quotation_values = {
                'name': '/',
                'partner_id': data['partner_id'][0],
                'date_livraison': data['delivery_date_max'],
                'date_expedition': date_expedition,
                'order_line': lines,
                'picking_policy': 'direct',
                'order_policy': 'picking',
                'invoice_quantity': 'order',
            }

            quotation.update(quotation_values)
            sale_id = sale_obj.create(cr, uid, quotation, context=context)
            res1 = sale_obj.action_button_confirm(cr, uid, [sale_id], context=context)

            #Supprimer les devis utilisés dans l'assistant pour créer la commande de vente
            sale_obj.unlink(cr, uid, sale_ids, context=context)
            
            # Mettre à jour la date de création de bon de livraison et afficher le bon de livraison
            # la date de création de bon de livraison = date de bon de livraison entrée dans le wizard
            result = sale_obj.action_view_delivery(cr, uid, [sale_id], context=context)
            picking = stock_obj.browse(cr, uid, result['res_id'], context=context)
            stock_obj.write(cr, uid, [picking.id], {'date':data['picking_date']}, context=context)

            return result
                                        
is_generate_picking_out()                
            

        
        
