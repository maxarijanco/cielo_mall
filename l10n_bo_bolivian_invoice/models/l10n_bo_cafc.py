# -*- coding:utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class L10nBoCafc(models.Model):
    _name="l10n.bo.cafc"
    _description="Codigo de autorización de facturas de contingencia"

    
    name = fields.Char(
        string='Codigo',
        copy=False,
        required=True
    )
    
    
    from_sequence = fields.Integer(
        string='Desde',
        copy=False,
        required=True
    )
    
    to_sequence = fields.Integer(
        string='Hasta',
        copy=False,
        required=True
    )

    
    actual_sequence = fields.Integer(
        string='Secuencia actual',
        help='Secuencia actual que se incrementa cuando se emite una factura con cafc'        
    )

    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        default= lambda self: self.getDefaultBranchOffice()
    )
    def getDefaultBranchOffice(self):
        branch_office = self.env['l10n.bo.branch.office'].search([], limit=1)
        return branch_office.id if branch_office else False

    
    economic_activity_id = fields.Many2one(
        string='Actividad',
        comodel_name='l10n.bo.activity',
    )
    

    
    
    document_type_id = fields.Many2one(
        string='Documento sector',
        comodel_name='l10n.bo.document.type',
    )
    
    @api.constrains('from_sequence')
    def _check_from_sequence(self):
        for record in self:
            if record.actual_sequence == 0:
                record.write({'actual_sequence' : record.from_sequence})
    
    
    def next_sequence(self):
        if self.actual_sequence<= self.to_sequence:
            self.write({'actual_sequence' : self.actual_sequence + 1})
        else:
            raise UserError(f'Ha llegado al final de la secuencia para el cafc:{self.name}')
    
    
    company_id = fields.Many2one(
        string='Compañia', 
        comodel_name='res.company', 
        required=True, 
        default=lambda self: self.env.company
    )

    def getCode(self):
        return self.name
    
    
    
    @api.constrains('name', 'from_sequence', 'to_sequence')
    def _check_name(self):
        for record in self:
            record.already_cafc(record.name, record.from_sequence, record.to_sequence)
            
    
    def already_cafc(self, _cafc, _from, _to):
        if _cafc in [None, False, '']:
            raise UserError("No puede iniciar su codigo vacio")
        
        if _from == 0 or _to == 0:
            raise UserError("No puede iniciar sus rango con ceros '0'")

        #cafc_ids = self.search([('company_id','=', self.env.company.id),('id','!=', self.id) ])
        #for cafc_id in cafc_ids:
        #        if cafc_id.name == _cafc:
        #            raise UserError(f'Ya exise un registro con el codigo: {_cafc}')
                

    def all_activities_inside(self, economic_activities):
        return economic_activities[0] == self.economic_activity_id.codigoCaeb
        #raise UserError(f"{economic_activities} - {[ activity.codigoCaeb for activity in self.economic_activity_ids]}")
        return all(
            [
                economic_activity in [ activity.codigoCaeb for activity in self.economic_activity_ids]
                for economic_activity in economic_activities
            ]
        )
    
    #def validateDocumentSector(self, sector):
    #    if sector.getCode() != self.document_type_id.getCode():
    #        raise UserError(f'El documento: {sector.name}, no tiene asignado un CAFC')