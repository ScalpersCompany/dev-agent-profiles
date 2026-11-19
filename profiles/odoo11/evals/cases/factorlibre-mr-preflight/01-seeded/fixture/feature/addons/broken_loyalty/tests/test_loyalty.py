from odoo.tests.common import TransactionCase


class TestLoyalty(TransactionCase):
    def test_code(self):
        card = self.env['loyalty.card'].create({'code': 'T1'})
        self.assertEqual(card.code, 'T1')
