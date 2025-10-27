# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCountryState(models.Model):    
    
    _inherit = ['res.country.state']
    abbreviation = fields.Char(
        string='Abreviatura',
        copy=False
    )
    

class ResCity(models.Model):
    _inherit = ['res.city']
    
    code = fields.Char(
        string='Codigo INE',
        copy=False
    )

class ResMunicipality(models.Model):
    _name = 'res.municipality'
    _description = 'Municipios de Bolivia'
    
    name = fields.Char(
        string='Nombre',
        copy=False
    )

    city_id = fields.Many2one(
        string='Provincia',
        comodel_name='res.city',
        copy=False
    )
    
    code = fields.Char(
        string='Codigo INE',
        copy=False
    )

    
    department_id = fields.Many2one(
        string='Departamento',
        comodel_name='res.country.state',
        copy=False
    )
