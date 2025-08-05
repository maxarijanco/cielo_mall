# -*- coding: utf-8 -*-

from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)



class AccountMoveLine(models.Model):
    _inherit = ['account.move.line']
    
    def group_in_taxs(self, column_rc_type):
        ON_TAX = len( [ tax_id for tax_id in self.tax_ids if tax_id.tax_group_id.column_rc_type == column_rc_type ] ) > 0
        return ON_TAX