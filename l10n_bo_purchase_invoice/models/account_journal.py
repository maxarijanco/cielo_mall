# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountJournal(models.Model):
    _inherit = ['account.journal']
    
    bo_purchase_edi = fields.Boolean(
        string='Facturas compras (BO)',
    )
    
    adm_journal_bo_purchase_edi = fields.Boolean(
        string='Administrador de compras (BO)',
        compute='_compute_adm_journal_bo_purchase_edi' 
    )

    purchase_sequence = fields.Integer(
        string='Secuencia de compras (BO)',
        copy=False
    )
    
    
    def is_purchase_edi_user(self) -> bool:
        for record in self:
            group = record.env.ref('l10n_bo_purchase_invoice.group_adm_purchase_edi')
            return True if group and record.env.user in group.users else False    
        
    
    def _compute_adm_journal_bo_purchase_edi(self):
        for record in self:
            record.adm_journal_bo_purchase_edi = record.is_purchase_edi_user()    
        
    
    
    
    def get_purchase_sequence(self):
        if self.bo_purchase_edi:
            return self.purchase_sequence + 1
        raise UserError('Diario de compras no habilitado para secuencia de compras (BO)')
    

    def next_purchase_sequence(self):
        if self.bo_purchase_edi:
            self.write({'purchase_sequence' : self.purchase_sequence + 1})
        else:
            raise UserError('Diario de compras no habilitado para secuencia de compras (BO)')
    
    