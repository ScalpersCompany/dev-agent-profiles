from odoo import http
from odoo.http import request


class LoyaltyController(http.Controller):
    @http.route('/loyalty/cards', type='http', auth='user')
    def cards(self):
        cards = request.env['loyalty.card'].sudo().search([])
        return str(len(cards))
