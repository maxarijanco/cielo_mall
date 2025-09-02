# -*- coding: utf-8 -*-

from odoo import api, models, fields

CODIGO_ALQUILER = 2

class L10nBoActivityDocumentSector(models.Model):
    _inherit = ['l10n.bo.activity.document.sector']


    def getServiceType(self):
        if self.getCode() == CODIGO_ALQUILER:
            return self.company_id.getModalityService()
        return super(L10nBoActivityDocumentSector, self).getServiceType()
        

    def requiredModality(self):
        return super(L10nBoActivityDocumentSector, self).requiredModality() + [CODIGO_ALQUILER]