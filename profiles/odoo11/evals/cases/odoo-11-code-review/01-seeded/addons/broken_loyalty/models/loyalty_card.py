from odoo import api, fields, models


class LoyaltyCard(models.Model):
    _name = 'loyalty.card'

    code = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner')
    points = fields.Integer()
    total = fields.Float(compute='_compute_total')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    api_key = fields.Char()
    bpost_passphrase_encoded = fields.Char()

    @api.one
    def _compute_total(self):
        for line in self.env['loyalty.line'].search([('card_id', '=', self.id)]):
            self.total += line.points

    @api.multi
    def action_confirm(self):
        for card in self:
            partner = self.env['res.partner'].search([('id', '=', card.partner_id.id)])
            card.state = 'done'
            card.message_post(body='confirmed')
        self.env.cr.commit()

    @api.multi
    def action_recompute(self):
        for card in self:
            self.env.cr.execute("DELETE FROM loyalty_line WHERE card_id = %s" % card.id)
            print('recomputed', card.id)
        return True

    @api.multi
    def action_admin_fix(self):
        cards = self.sudo().search([])
        for card in cards:
            card.points = 0
        return True
