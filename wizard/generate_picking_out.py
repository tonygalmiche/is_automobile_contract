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
        'date_livraison': fields.date('Date Livraison', readonly=True, required=True),
        'date_expedition': fields.date('Date Expedition', readonly=True, required=True),
        'product_id': fields.many2one('product.product', 'Produit', required=True),
        'picking_id': fields.many2one('is.picking.out', 'Reference', required=True, ondelete='cascade', select=True, readonly=True),
        'quantity': fields.float('Quantite'),
        'sale_id': fields.integer('ID devis', readonly=True),
        'line_id': fields.integer('ID line', readonly=True),
    }

is_quotation_line()


class is_generate_picking_out(osv.osv_memory):

    _name = "is.picking.out"
    _description = "Generate picking out"
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Client', required=True),
        'expedition_date_max': fields.date('Date expedition maxi', required=True),
        'picking_date': fields.date('Date de bon de livraison', required=True),
        'quotation_lines': fields.one2many('is.quotation.line', 'picking_id', 'Commandes', required=True),
    }
    
    _defaults = {
        'expedition_date_max': fields.date.context_today,
        'picking_date': fields.date.context_today,
    }

    def get_quotations(self, cr, uid, partner_id, date_max, context=None):
        cr.execute("SELECT line.product_id, line.product_uom_qty, sale.date_expedition, sale.date_livraison, sale.id, line.id " \
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
                    'line_id': item[5],
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

    def clean_quotations(self, cr, uid, sale_id, line_id, qty, context=None):
        order_line_obj = self.pool.get('sale.order.line')
        order_obj = self.pool.get('sale.order')

        line = order_line_obj.browse(cr, uid, line_id, context=context)
        if qty < line.product_uom_qty:
            diff = line.product_uom_qty - qty
            order_line_obj.write(cr, uid, [line_id], {'product_uom_qty': diff}, context=context)
        else:
            order_line_obj.unlink(cr, uid, [line_id], context=context)
            if len(order_obj.browse(cr, uid, sale_id, context=context).order_line) == 0:
                order_obj.unlink(cr, uid, [sale_id], context=context)
            else:
                pass
        return True                  
                

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
            for line in quotation_line_obj.browse(cr, uid, data['quotation_lines'], context=context):
                quotation_line = order_line_obj.product_id_change(cr, uid, ids, 1, line.product_id.id, 0, False, 0, False, '', data['partner_id'][0], False, True, False, False, False, False, context=context)['value']
                quotation_line.update({'product_id':line.product_id.id, 'product_uom_qty': line.quantity})
                lines.append([0,False,quotation_line])

                #Nettoyage des devis
                self.clean_quotations(cr, uid, line.sale_id, line.line_id, line.quantity, context=context)

            #create quotation
            quotation = sale_obj.onchange_partner_id(cr, uid, ids, data['partner_id'][0], context=context)['value']
            date_expedition = sale_obj.onchange_date_livraison(cr, uid, ids, data['expedition_date_max'], data['partner_id'][0], context=context)['value']['date_expedition']
            quotation_values = {
                'name': '/',
                'partner_id': data['partner_id'][0],
                'date_livraison': data['expedition_date_max'],
                'date_expedition': date_expedition,
                'order_line': lines,
                'picking_policy': 'direct',
                'order_policy': 'manual',
                'invoice_quantity': 'order',
            }

            quotation.update(quotation_values)
            sale_id = sale_obj.create(cr, uid, quotation, context=context)
            res1 = sale_obj.action_button_confirm(cr, uid, [sale_id], context=context)
            

            # Mettre à jour la date de création de bon de livraison et afficher le bon de livraison
            # la date de création de bon de livraison = date de bon de livraison entrée dans le wizard
            result = sale_obj.action_view_delivery(cr, uid, [sale_id], context=context)
            picking = stock_obj.browse(cr, uid, result['res_id'], context=context)
            stock_obj.write(cr, uid, [picking.id], {'date':data['picking_date']}, context=context)

            return result
                                        
is_generate_picking_out()
