# -*- coding: utf-8 -*-

from odoo import api, models, fields


class L10nBoActivityDocumentSector(models.Model):
    _inherit = ['l10n.bo.activity.document.sector']


    def getServiceType(self):
        if self.getCode() == 23:
            return self.company_id.getModalityService()
        return super(L10nBoActivityDocumentSector, self).getServiceType()
        

    def requiredModality(self):
        return super(L10nBoActivityDocumentSector, self).requiredModality() + [23]