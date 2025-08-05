# -*- coding:utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError

class ValidateAccountMove(models.TransientModel):
    _inherit = ['validate.account.move']
    
    
    mails_send = fields.Boolean(
        string='Enviar correo',
        default=False
    )
    
    def validate_move(self):
        if self._context.get('active_model') == 'account.move':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
        elif self._context.get('active_model') == 'account.journal':
            domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        else:
            raise UserError(_("Missing 'active_model' in context."))

        moves = self.env['account.move'].search(domain).filtered('line_ids')
        
        if moves and not self.mails_send:
            moves.write({'email_send' : self.mails_send})

        res = super(ValidateAccountMove, self).validate_move()
        return res
        # if self._context.get('active_model') == 'account.move':
        #     domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
        # elif self._context.get('active_model') == 'account.journal':
        #     domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        # else:
        #     raise UserError(_("Missing 'active_model' in context."))

        # moves = self.env['account.move'].search(domain).filtered('line_ids')
        # if not moves:
        #     raise UserError(_('There are no journal items in the draft state to post.'))
        # if self.force_post:
        #     moves.auto_post = 'no'
        # if moves:
        #     moves.write({'email_send' : self.mails_send})
        # moves._post(not self.force_post)
        # return {'type': 'ir.actions.act_window_close'}

    