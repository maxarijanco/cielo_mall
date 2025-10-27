# -*- coding: utf-8 -*-

from . import models


from odoo import api, SUPERUSER_ID
from odoo.tools import convert_file
import os

def load_toponyms(env):
    
    # Verificar si ya existe el primer estado en el módulo anterior
    exists = env.ref("l10n_bo_bolivian_invoice.l10n_bo_state_01", raise_if_not_found=False)
    if exists:
        refs = env['ir.model.data'].search([
            ('module', '=', 'l10n_bo_bolivian_invoice'),
            ('model', '=', 'res.country.state')
        ])
        refs.write({'model' : 'l10n_bo_toponyms'})
        
        refs = env['ir.model.data'].search([
            ('module', '=', 'l10n_bo_bolivian_invoice'),
            ('model', '=', 'res.city')
        ])
        refs.write({'model' : 'l10n_bo_toponyms'})
        
        refs = env['ir.model.data'].search([
            ('module', '=', 'l10n_bo_bolivian_invoice'),
            ('model', '=', 'res.municipality')
        ])
        refs.write({'model' : 'l10n_bo_toponyms'})
        

        
        return  # Ya existen, no hacemos nada

    # Si no existe, cargamos el CSV con el motor nativo de Odoo
    module_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(module_path, "data", "res.country.state.csv")

    convert_file(
        env,
        "l10n_bo_toponyms",   # nombre técnico de tu módulo nuevo
        csv_path,
        None,                 # idref (None = sin referencias externas adicionales)
        mode="init",          # init = como si fuera un install
        noupdate=True,
        kind="data"
    )

    res_city = os.path.join(module_path, "data", "res.city.csv")

    convert_file(
        env,
        "l10n_bo_toponyms",   # nombre técnico de tu módulo nuevo
        res_city,
        None,                 # idref (None = sin referencias externas adicionales)
        mode="init",          # init = como si fuera un install
        noupdate=True,
        kind="data"
    )

    res_municipality = os.path.join(module_path, "data", "res.municipality.csv")

    convert_file(
        env,
        "l10n_bo_toponyms",   # nombre técnico de tu módulo nuevo
        res_municipality,
        None,                 # idref (None = sin referencias externas adicionales)
        mode="init",          # init = como si fuera un install
        noupdate=True,
        kind="data"
    )
    



def _post_init(env):
    load_toponyms(env)