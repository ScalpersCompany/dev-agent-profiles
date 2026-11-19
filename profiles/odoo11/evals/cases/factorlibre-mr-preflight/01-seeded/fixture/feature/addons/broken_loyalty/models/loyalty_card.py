import pdb
from datetime import datetime

from odoo import api, fields, models
from odoo.addons.mail.models import mail_thread  # noqa: F401


class LoyaltyCard(models.Model):
    _name = 'loyalty.card'

    code = fields.Char(required=True)
    points = fields.Integer()
    total = fields.Float(compute='_compute_total')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    api_key = fields.Char()
    bpost_passphrase_encoded = fields.Char()

    @api.one
    def _compute_total(self):
        for line in self.env['loyalty.line'].search([('card_id', '=', self.id)]):
            self.total += line.points

    def action_debug(self):
        print('debug', self.id)
        pdb.set_trace()
        eval("1 + 1")
        card_code = f"card-{self.id}"
        self.env['res.partner'].search([])
        self.env.cr.commit()
        return datetime.now()
