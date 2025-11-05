# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command

from odoo.addons.stock_reserve_rule.tests.common import ReserveRuleCommon


class TestReserveRuleFull(ReserveRuleCommon):
    def test_reserve_rule_full(self):
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 100)
        picking = self._create_picking(self.wh, [(self.product1, 250)])
        self._create_rule(
            {},
            [
                {
                    "location_id": self.loc_zone3.id,
                    "sequence": 1,
                    "removal_strategy": "full_demand",
                },
            ],
        )

        picking.action_assign()
        move = picking.move_ids
        ml = move.move_line_ids
        self.assertFalse(ml)

        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 300)
        picking.action_assign()
        ml = move.move_line_ids
        self.assertTrue(ml)

    def test_reserve_rule_full_fallback(self):
        """
        This is the test where the picking location source should
        be reassigned to the zone 3
        """
        self._update_qty_in_location(self.loc_zone2_bin1, self.product1, 100)
        self._update_qty_in_location(self.loc_zone3_bin1, self.product1, 10)
        picking = self._create_picking(
            self.wh, [(self.product1, 250)], location_src_id=self.loc_zone2.id
        )
        self._create_rule(
            {},
            [
                {
                    "location_id": self.loc_zone2.id,
                    "sequence": 1,
                    "removal_strategy": "full_demand",
                    "full_demand_fallback_location_ids": [
                        Command.link(self.loc_zone3_bin1.id)
                    ],
                },
            ],
        )

        picking.action_assign()
        move = picking.move_ids
        ml = move.move_line_ids
        self.assertFalse(ml)
