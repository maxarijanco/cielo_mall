# -*- coding: utf-8 -*-

from . import models


def sync_purchase_services(env):
    purchase_service_pilot = env.ref('l10n_bo_purchase_invoice_register.l10n_bo_wsdl_purchase_reception_2', False)
    if purchase_service_pilot:
        purchase_service_pilot.operation_service_soap()
    
    purchase_service_prd = env.ref('l10n_bo_purchase_invoice_register.l10n_bo_wsdl_purchase_reception_1', False)
    if purchase_service_prd:
        purchase_service_prd.operation_service_soap()
    

def _post_init(env):
    sync_purchase_services(env)