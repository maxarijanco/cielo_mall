# -*- coding: utf-8 -*-

from odoo import api, models, fields

class L10nB0PackageLine(models.Model):
    _inherit = ['l10n.bo.package.line']
    
    # def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
    #     if self.document_type_id.getCode() == 3:
    #         MODALITY_TYPE = self.company_id.getL10nBoCodeModality()    
    #     return super(L10nB0PackageLine, self).soap_service(METHOD, SERVICE_TYPE, MODALITY_TYPE)