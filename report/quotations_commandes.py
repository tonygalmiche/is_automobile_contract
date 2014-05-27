# -*- coding: utf-8 -*-

from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_sale_quotation(osv.osv):
    _name = "report.sale.quotation"
    _description = "quotations"
    _auto = False
    _columns = {
        'partner_id':fields.many2one('res.partner', 'Client', readonly=True),
        'name':fields.char('Numero', size=64, readonly=True),
        'product_id':fields.many2one('product.product', 'Article', readonly=True),
        'date_order': fields.date('Date commande', readonly=True),
        'date_expedition': fields.date('Date expedition', readonly=True),
        'date_livraison': fields.date('Date livraison', readonly=True),
        'quantity': fields.float('Quantite', readonly=True),
        'type': fields.selection([('ferme', 'Ferme'),('previsionnel', 'Previsionnel')], "Type", readonly=True, select=True),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Statut', readonly=True, select=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_sale_quotation')
        cr.execute("""
                CREATE OR REPLACE view report_sale_quotation AS (
                SELECT
                        min(line.id) as id,
                        sq.partner_id as partner_id,
                        sq.name as name,
                        line.product_id as product_id,
                        sq.date_order as date_order,
                        sq.date_livraison as date_livraison,
                        sq.date_expedition as date_expedition,
                        line.product_uom_qty as quantity,
                        sq.type_contrat as type,
                        sq.state as state
                    FROM
                        sale_order sq
                        INNER JOIN sale_order_line line ON (sq.id=line.order_id)
                    WHERE sq.state in ('draft', 'sent')
                    GROUP BY line.id, line.product_id, line.product_uom_qty, sq.name, sq.partner_id, sq.date_order, sq.date_livraison, sq.date_expedition, sq.type_contrat, sq.state
               )
        """)

report_sale_quotation()


class report_sale_commande(osv.osv):
    _name = "report.sale.commande"
    _description = "Commandes"
    _auto = False
    _columns = {
        'partner_id':fields.many2one('res.partner', 'Client', readonly=True),
        'name':fields.char('Numero', size=64, readonly=True),
        'product_id':fields.many2one('product.product', 'Article', readonly=True),
        'date_order': fields.date('Date commande', readonly=True),
        'date_expedition': fields.date('Date expedition', readonly=True),
        'date_livraison': fields.date('Date livraison', readonly=True),
        'quantity': fields.float('Quantite', readonly=True),
        'type': fields.selection([('ferme', 'Ferme'),('previsionnel', 'Previsionnel')], "Type", readonly=True, select=True),
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Statut', readonly=True, select=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_sale_commande')
        cr.execute("""
                CREATE OR REPLACE view report_sale_commande AS (
                SELECT
                        min(line.id) as id,
                        sq.partner_id as partner_id,
                        sq.name as name,
                        line.product_id as product_id,
                        sq.date_order as date_order,
                        sq.date_livraison as date_livraison,
                        sq.date_expedition as date_expedition,
                        line.product_uom_qty as quantity,
                        sq.type_contrat as type,
                        sq.state as state
                    FROM
                        sale_order sq
                        INNER JOIN sale_order_line line ON (sq.id=line.order_id)
                    WHERE sq.state = 'manual'
                    GROUP BY line.id, line.product_id, line.product_uom_qty, sq.name, sq.partner_id, sq.date_order, sq.date_livraison, sq.date_expedition, sq.type_contrat, sq.state
               )
        """)

report_sale_commande()
