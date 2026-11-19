from odoo.tests.common import TransactionCase


class TestLoyalty(TransactionCase):
    def test_confirm(self):
        card = self.env['loyalty.card'].create({'code': 'T1'})
        card.action_confirm()
        self.assertEqual(card.state, 'done')
