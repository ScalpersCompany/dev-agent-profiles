from odoo import fields, models


class LoyaltyLine(models.Model):
    _name = 'loyalty.line'
    _description = 'Loyalty line'

    card_id = fields.Many2one('loyalty.card')
    points = fields.Integer()
