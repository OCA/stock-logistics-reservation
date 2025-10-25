# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.fields import Command

from .common import DeliveryCarrierAlternativeCommon


class TestDeliveryCarrierAlternative(DeliveryCarrierAlternativeCommon):
    def test_no_alternative(self):
        """
        2 available to promise, weight is 20, but no alternative declared
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 2
        )
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 20.0)
        self.assertEqual(self.delivery.carrier_id, self.normal_carrier)

    def test_alternative_excluded(self):
        """
        4 available to promise, weight is 40, alternative not valid
        """
        self.set_alternatives()
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 4
        )
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 40.0)
        self.assertEqual(self.delivery.carrier_id, self.normal_carrier)

    def test_alternative_domain(self):
        """
        3 available to promise, weight is 30, second alternative excluded by domain
        """
        self.set_alternatives()
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        self.the_poste_carrier.picking_domain = "[('id', '=', 0)]"
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 30.0)
        self.assertEqual(self.delivery.carrier_id, self.normal_carrier)
        self.assertEqual(self.delivery.group_id.carrier_id, self.normal_carrier)
        backorder = self.delivery.backorder_ids
        self.assertEqual(backorder.carrier_id, self.normal_carrier)
        self.assertEqual(backorder.group_id.carrier_id, self.normal_carrier)

    def test_alternative_theposte(self):
        """
        3 available to promise, weight is 30, second alternative valid
        """
        self.set_alternatives()
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 30.0)
        self.assertEqual(self.delivery.carrier_id, self.the_poste_carrier)
        self.assertEqual(self.delivery.group_id.carrier_id, self.the_poste_carrier)
        backorder = self.delivery.backorder_ids
        self.assertEqual(backorder.carrier_id, self.normal_carrier)
        self.assertEqual(backorder.group_id.carrier_id, self.normal_carrier)

    def test_alternative_superfast(self):
        """
        2 available to promise, weight is 20, first alternative valid
        """
        self.set_alternatives()
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 2
        )
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 20.0)
        self.assertEqual(self.delivery.carrier_id, self.super_fast_carrier)
        self.assertEqual(self.delivery.group_id.carrier_id, self.super_fast_carrier)
        backorder = self.delivery.backorder_ids
        self.assertEqual(backorder.carrier_id, self.normal_carrier)
        self.assertEqual(backorder.group_id.carrier_id, self.normal_carrier)

    def test_no_backorder_no_alternative(self):
        """
        all available to promise, but no alternative declared
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 5
        )
        self.delivery.move_ids.rule_id.no_backorder_at_release = True
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 50.0)
        self.assertEqual(self.delivery.carrier_id, self.normal_carrier)
        self.assertFalse(self.delivery.backorder_id)

    def test_no_backorder_with_alternative(self):
        """
        all available to promise, but alternative declared
        """
        self.set_alternatives()
        self.the_poste_carrier.max_weight = 50
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 5
        )
        self.delivery.move_ids.rule_id.no_backorder_at_release = True
        self.delivery.release_available_to_promise()
        self.assertAlmostEqual(self.delivery.weight, 50.0)
        self.assertEqual(self.delivery.carrier_id, self.the_poste_carrier)
        self.assertFalse(self.delivery.backorder_id)

    def test_delivery_route_all(self):
        """
        all available to promise, carrier as a dedicated route
        """
        self.set_alternatives()
        self.the_poste_carrier.max_weight = 50
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 5
        )
        self.delivery.move_ids.rule_id.no_backorder_at_release = True
        route = self.wh.delivery_route_id.copy()
        delivery_rule = route.rule_ids.filtered(
            lambda r: r.location_dest_id
            == self.env.ref("stock.stock_location_customers")
        )
        delivery_rule.picking_type_id = self.wh.out_type_id.copy()
        self.the_poste_carrier.route_ids = [Command.set(route.ids)]
        moves = self.delivery.move_ids
        self.delivery.release_available_to_promise()
        self.assertEqual(self.delivery.state, "cancel")
        new_delivery = moves.picking_id
        self.assertAlmostEqual(new_delivery.weight, 50.0)
        self.assertEqual(new_delivery.carrier_id, self.the_poste_carrier)
        self.assertFalse(new_delivery.backorder_id)

    def test_delivery_route_partial(self):
        """
        partially available to promise, carrier as a dedicated route
        """
        self.set_alternatives()
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        self.delivery.move_ids.rule_id.no_backorder_at_release = True
        route = self.wh.delivery_route_id.copy()
        delivery_rule = route.rule_ids.filtered(
            lambda r: r.location_dest_id
            == self.env.ref("stock.stock_location_customers")
        )
        delivery_rule.picking_type_id = self.wh.out_type_id.copy()
        self.the_poste_carrier.route_ids = [Command.set(route.ids)]
        moves = self.delivery.move_ids
        self.delivery.release_available_to_promise()
        new_delivery = moves.picking_id
        self.assertEqual(new_delivery.need_release, False)
        self.assertEqual(new_delivery.carrier_id, self.the_poste_carrier)
        self.assertAlmostEqual(new_delivery.weight, 30.0)
        self.assertEqual(self.delivery.carrier_id, self.normal_carrier)
        self.assertAlmostEqual(self.delivery.weight, 20.0)
        self.assertEqual(self.delivery.backorder_id.backorder_id, new_delivery)
