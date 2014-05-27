# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _


class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'delai_transport': fields.integer('Delai de transport (jour)'),
    }

    _defaults = {
        'delai_transport': 0,
    }
    

res_partner()
