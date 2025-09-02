# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError
import pytz
from datetime import datetime, timedelta
from num2words import num2words
import qrcode
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
    _inherit = ['account.move']
    
    
    edi_bo_invoice = fields.Boolean(
        string='Factura (BO)',
        related='journal_id.bo_edi',
        readonly=True,
        store=True
    )
    
    
    
    branch_office_id = fields.Many2one(
        string='Sucursal',
        comodel_name='l10n.bo.branch.office',
        ondelete='restrict',
        default= lambda self : self.get_branch_office_default()
    )


    @api.model
    def create(self, values):
        account_move_id = super(AccountMove, self).create(values)
        account_move_id.prepare_fields()
        return account_move_id
    

    
    #@api.onchange('move_type')
    #@api.constrains('move_type')
    def prepare_fields(self):
        for record in self:
            if record.edi_bo_invoice:
                record.write( {'branch_office_id' : record.get_branch_office_default() } )
                record._set_default_pos_id()
                
    def get_branch_office_default(self):
        branch_office_id = self.env.company.branch_office_id
        return branch_office_id.id if branch_office_id else False 
    
    @api.onchange('pos_id')
    def _onchange_pos_id(self):
        if self.pos_id:
            self.document_type_id = self.pos_id.default_sequence_id
    
    
    
    pos_id = fields.Many2one(
        string='Punto de venta',
        comodel_name='l10n.bo.pos',
    )
    
    @api.constrains('pos_id')
    def _check_pos_id(self):
        for record in self:
            if record.pos_id:
                record.emision_type_id = record.pos_id.emision_id.id if record.pos_id.emision_id else False
    

    
    emision_type_id = fields.Many2one(
        string='Tipo emisión',
        comodel_name='l10n.bo.type.emision',
    )

    
    emision_code = fields.Integer(
        related='emision_type_id.codigoClasificador',
        readonly=True,
        store=True    
    )
    
    
    
    many_pos = fields.Boolean(
        string='Muchas puntos de venta',
        compute='_compute_many_pos', 
    )
    
    def _compute_many_pos(self):
        for record in self:
            record.many_pos = True if len(record.env['l10n.bo.pos'].search([])) > 1 else False
    
    
    @api.onchange('branch_office_id')    
    #@api.constrains('branch_office_id')
    def _set_default_pos_id(self):
        for record in self:
            if record.branch_office_id and not record.pos_id:
                record.write( { 'pos_id' :  record.branch_office_id.default_pos_id.id if record.branch_office_id and record.branch_office_id.default_pos_id else False } ) 
            record._set_default_document_type()
        
    
    meridies = fields.Selection(
        string='Meridiano',
        selection=[('am', 'AM'), ('pm', 'PM')]
    )
    

    
    invoice_date_edi = fields.Datetime(
        string='Fecha y hora (BO)',
        default=fields.Datetime.now,
        copy=False
    )
    
    
    # @api.constrains('invoice_date_edi')
    # def _check_invoice_date_edi(self):
    #     for record in self:
    #         if record.edi_bo_invoice and record.move_type in ['out_invoice','out_refund']:
    #             record.write({'invoice_date' : fields.Date.context_today(self)})
    
    # REVISAR METODO
    def get_formatted_datetime(self):
        if self.invoice_date_edi:
            emision_date_utc = self.invoice_date_edi.replace(tzinfo=None).astimezone(pytz.UTC)
            # Restar 4 horas a la fecha y hora
            emision_date_minus_4_hours = emision_date_utc - timedelta(hours=4)
            return emision_date_minus_4_hours.strftime("%d/%m/%Y %I:%M")
        else:
            return ''

    
    document_type_id = fields.Many2one(
        string='Tipo documento',
        comodel_name='l10n.bo.pos.sequence',
    )

    
    l10n_bo_document_type = fields.Many2one(
        comodel_name='l10n.bo.document.type',
        related='document_type_id.name',
        readonly=True,
        store=True
    )
    
    document_type_code = fields.Integer(
        string='Código de documento',
        related='l10n_bo_document_type.codigoClasificador',
        readonly=True,
        store=True   
    )
    

    invoice_type_id = fields.Many2one(
        comodel_name='l10n.bo.type.invoice',
        related='l10n_bo_document_type.invoice_type_id',
        readonly=True,
        store=True
        
    )
    
    

    


    invoice_type_code = fields.Integer(
        string='Codigo tipo factura',
        related='invoice_type_id.codigoClasificador',
        readonly=True,
        store=True
        
    )
    

    
    #@api.onchange('move_type', 'edi_bo_invoice')
    def _set_default_document_type(self):
        for record in self:
            #raise UserError(f"{record.edi_bo_invoice} - {record.move_type}")
            if record.edi_bo_invoice and record.pos_id:
                doc_type_id = False
                
                #raise UserError(record.move_type)
                if record.move_type == 'out_invoice':
                    #dt = record.pos_id.sequence_ids.filtered(lambda document_type_sequence : document_type_sequence.name.invoice_type_id.getCode() in [1,2,4])
                    if record.pos_id.default_sequence_id:
                        doc_type_id = record.pos_id.default_sequence_id.id #sequence_ids.filtered(lambda s:s.name.invoice_type_id.getCode() in [1,2,4])[0].id
                        #for sequence_id in record.pos_id.sequence_ids:
                        #    if sequence_id.name.invoice_type_id.getCode() in [1,2,4]:
                        #        doc_type_id = sequence_id.id
                        #        break
                
                elif record.move_type == 'out_refund':
                    if record.reversed_entry_id and record.reversed_entry_id.getAmountDiscount()>0:
                        dt = record.pos_id.sequence_ids.filtered(lambda document_type_sequence : document_type_sequence.getCode() == 47)[:1]
                        if dt and record.document_type_id and record.document_type_id.name.invoice_type_id.getCode() != 3 :
                            doc_type_id = dt.id
                            record.write({'document_type_id' : doc_type_id})
                    
                    else:
                        dt = record.pos_id.sequence_ids.filtered(lambda document_type_sequence : document_type_sequence.getCode() == 24)[:1]
                        if dt and record.document_type_id and record.document_type_id.name.invoice_type_id.getCode() != 3 :
                            doc_type_id = dt.id
                            record.write({'document_type_id' : doc_type_id})
                
                if doc_type_id and not record.document_type_id:
                    record.write({'document_type_id' : doc_type_id})
        

    
    payment_type_id = fields.Many2one(
        string='Tigo pago',
        comodel_name='l10n.bo.type.payment',
        ondelete='restrict',
        default= lambda self : self.get_payment_type_default()
    )
    
    def get_payment_type_default(self):
        payment_type = self.env['l10n.bo.type.payment'].search([('codigoClasificador','=',1)], limit=1)
        return payment_type.id if payment_type  else False
    

    
    error = fields.Text(
        string='Error',
        copy=False,
        readonly=True
    )
    
    
    legend_id = fields.Many2one(
        string='Leyenda',
        comodel_name='l10n.bo.legend.code',
        #ondelete='restrict',
        #default= lambda self : self.get_legend_default()
    )
    
    
    #@api.onchange('company_id')
    #@api.constrains('company_id')
    #def _check_company_id(self):
    #    for record in self:
    #        _logger.info(f"Compañia: {record.company_id.getGrandParent().name}")
    #        if not record.legend_id and record.company_id:
    #            record.write({'legend_id' : record.get_legend_default(record.company_id.getGrandParent().id)})
    
    
    
    amount_payment_gifcard_plus = fields.Float(
        string='Monto gifcard',
        copy=False
    )

    
    @api.onchange('amount_payment_gifcard_plus')
    
    @api.constrains('amount_payment_gifcard_plus')
    def _check_amount_payment_gifcard_plus(self):
        for record in self:
            record.getAmountGiftCard()
            
    
    
    
    amount_giftcard = fields.Float(
        string='Monto total Giftcard',
        copy=False
    )


    def getAmountGiftCard(self):
        amount = 0
        if self.is_gift_card:
            ld = self.invoice_line_ids.filtered(lambda l: l.product_id.gift_card_product)
            
            if not ld:
                self.write({'amount_giftcard' : 0.0})
            elif ld:
                
                for l in ld:
                    amount += l.price_unit * -1
            amount += self.amount_payment_gifcard_plus
            self.write({'amount_giftcard' : amount})
            
            amount = round(self.amount_giftcard * self.currency_id.getExchangeRate() , self.decimalbo())

            return  amount
        return 0
        
    

    is_gift_card = fields.Boolean(
        string='¿Es gift card?',
    )
    
    @api.onchange('payment_type_id')
    def _compute_is_gift_card(self):
        for record in self:
            is_gift_card = False
            if record.payment_type_id and 'GIFT' in record.payment_type_id.descripcion:
                is_gift_card = True
            record.write({'is_gift_card' :  is_gift_card})
    
    card = fields.Char(
        string='Tarjeta',
        size=16
    )
    

    is_card = fields.Boolean(string='¿Es tarjeta?' )
    
    @api.onchange('payment_type_id')
    @api.constrains('payment_type_id')
    def _onchange_payment_type_id(self):
        for record in self:
            is_card = False
            if record.payment_type_id and 'TARJETA' in record.payment_type_id.descripcion:
                is_card = True
            record.write({'is_card':is_card}) 
    
    def decimalbo(self)->int:
        "Precision decimales"
        return 2
    
    @api.model
    def decimallinebo(self)->int:
        return self.env['account.move.line'].decimalbo()
    
    # DESCLARAR CAMPO
    invoice_number = fields.Float(
        string='Nro. Factura',
        copy=False, 
        digits=(20, 0)
    )
    
    
    force_send = fields.Boolean(
        string='Forzar envio',
        copy=False,
        help='Activar para enviar factura con codigo de excepción 1'
    )

    
    email_send = fields.Boolean(
        string='Enviar correo',
        default=True
    )
    

    
    nit_state = fields.Char(
        string='Estado del nit',
        related='partner_id.nit_state',
        readonly=True,
        store=True
    )
    
    
    
    # CAMPO A ELIMINAR
    cuf = fields.Char(
        string='CUF',
        help='Codigo unico de facturación.',
        copy=False,
    )
    
    # CAMPO A ELIMINAR
    edi_str = fields.Text(
        string='Formato edi',
        copy=False,
        readonly=True 
    )
    
    # Eliminar campo *
    sector_document_id = fields.Many2one(
        string='Documento sector',
        comodel_name='l10n.bo.activity.document.sector',
        related='document_type_id.name.sector_document_id',
        readonly=True,
        store=True,
    )
    
    signed_edi_str = fields.Binary(
        string='Formato edi firmado',
        copy=False,
        readonly=True 
    )

    zip_edi_str = fields.Binary(
        string='Documento ZIP',
        copy=False,
        readonly=True 
    )

    
    
    hash = fields.Binary(
        string = 'HASH',
        copy=False,
        readonly=True 
    )


    
    url = fields.Char(
        string='url',
        copy=False,
        readonly=False
    )
    
    edi_state = fields.Char(
        string='Estado edi',
        copy=False,
        readonly=True 
    )
    
    
    transaccion = fields.Boolean(
        string='Transacción',
        readonly=True,
        copy=False
    )
    
    
    codigoEstado = fields.Integer(
        string='Codigo de estado',
        copy=False
    )
    
    
    codigoRecepcion = fields.Char(
        string='Codigo recepción',
        copy=False
    )
    
    messagesList_ids = fields.One2many(
        string='Lista de mensajes',
        comodel_name='message.code',
        inverse_name='account_move_id',
        copy=False
    )


    
    code_environment = fields.Selection(
        string='Codigo de entorno',
        related='company_id.l10n_bo_code_environment',
        readonly=True,
        store=True
    )
    
    def getLiteral(self):
        parte_entera = int(self.amountCurrency())
        parte_decimal = int( (self.amountCurrency() - parte_entera) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        return num2words(parte_entera, lang='es') + parte_decimal +'/100'
    
    def getBolivianLiteral(self):
        
        amount_total = self.getAmountTotal() if self.document_type_id.name.invoice_type_id.getCode() == 2 else self.getAmountOnIva()  # * self.currency_id.getExchangeRate()
        
        #VERIFICAR
        #if self.document_type_code in [14]:
        #    amount_total += self.getAmountSpecificIce() + self.getAmountPercentageIce()

        parte_entera = int(amount_total)
        parte_decimal = int( (amount_total - parte_entera) *100)
        parte_decimal = f' {parte_decimal}' if parte_decimal > 10 else f' 0{parte_decimal}'
        return num2words(parte_entera, lang='es') + parte_decimal +'/100'
    
    
    
    
    

    def generate_qr(self):
            image = qrcode.make(
                f"{self.url}"
            ).get_image()
            buff = BytesIO()
            image.save(buff, format="PNG")
            return base64.b64encode(buff.getvalue()).decode('utf-8')
    

    
    success = fields.Boolean(
        string='Realizado',
        copy=False,
        readonly=True 
    )
    
    def showMessage(self, title, body):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'{title}',
                'message': f'{body}',
                'sticky': False,
            }
        }

    @api.model
    def get_datetime_bo(self):
        # Realizar la consulta SQL
        self.env.cr.execute("""
            SELECT current_timestamp AT TIME ZONE 'America/La_Paz'
        """)
        
        # Obtener el resultado de la consulta
        result = self.env.cr.fetchone()

        # El resultado estará en el índice 0
        datetime_bo = result[0] if result else None

        return datetime_bo
    
    def get_datetime(self):
        # Obtener la fecha y hora actual en la zona horaria de Bolivia (America/La_Paz)
        tz_bolivia = pytz.timezone('America/La_Paz')
        current_datetime = datetime.now(tz_bolivia)

        # Convertir el objeto datetime a UTC antes de asignarlo al campo
        current_datetime_utc = current_datetime.astimezone(pytz.UTC)

        # Eliminar la información de la zona horaria (convierte el objeto a "ingenuo")
        current_datetime_naive = current_datetime_utc.replace(tzinfo=None)

        return current_datetime_naive
    
    
    manual_invoice = fields.Boolean(
        string='Factura manual - CAFC',
    )
    
    cafc = fields.Char(
        string='CAFC',
        help='Codigo de autorizacion de facturas de contingencia'
    )
    
    
    economic_activity_id = fields.Many2one(
        string='Actividad economica',
        comodel_name='l10n.bo.activity',
    )
    

    def invisible_for_moves(self):
        return super(AccountMove, self).invisible_for_moves() + ['out_invoice']
        