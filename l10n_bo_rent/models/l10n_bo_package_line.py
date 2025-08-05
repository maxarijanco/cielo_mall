# -*- coding: utf-8 -*-

from odoo import api, models, fields

class L10nB0PackageLine(models.Model):
    _inherit = ['l10n.bo.package.line']
    
    def soap_service(self, METHOD = None, SERVICE_TYPE = None, MODALITY_TYPE = None):
        if self.document_type_id.getCode() == 2:
            if self.company_id.getL10nBoCodeModality() == '1':
                SERVICE_TYPE = 'ServicioFacturacionElectronica'
            elif self.company_id.getL10nBoCodeModality() == '2':
                SERVICE_TYPE = 'ServicioFacturacionComputarizada'
            
        return super(L10nB0PackageLine, self).soap_service(METHOD, SERVICE_TYPE, MODALITY_TYPE)
        