# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from .common import PRIORITY_NORMAL, DeliveryCarrierPreferenceCommon


class TestSaleDeliveryCarrierPreference(DeliveryCarrierPreferenceCommon):
    def test_hooks(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        delivery_pick = self._create_out_picking(product_qty=[(self.product1, 5)])
        delivery_pick.invalidate_recordset()  # force recompute
        # Ensure _get_processed_quantity overrides values
        # from hooks in stock_picking_volume and delivery_total_weight_from_packaging
        self.assertAlmostEqual(delivery_pick._get_estimated_weight(), 30.0)
        self.assertAlmostEqual(delivery_pick.volume, 30.0)

    def test_delivery_add_preferred_carrier(self):
        """
        With a qty of 5 in the sale order and only 3 available to promise,
        estimated_shipping_weight is 30, and preferred carrier 'the poste'
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        delivery_pick = self._create_out_picking(product_qty=[(self.product1, 5)])
        self.assertAlmostEqual(delivery_pick._get_estimated_weight(), 30.0)
        delivery_pick._apply_alternative_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.the_poste_carrier)

    def test_delivery_release_available_to_promise(self):
        """
        With carrier 'super fast' and a qty of 3 required,
        only 2 available to promise, estimated_shipping_weight is 20.0,
        so preferred carrier after the release is 'normal' and backorder get
        'super fast'
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 2
        )
        delivery_pick = self._create_out_picking(
            product_qty=[(self.product1, 3)], carrier=self.super_fast_carrier
        )
        self.assertAlmostEqual(delivery_pick._get_estimated_weight(), 20.0)
        delivery_pick.release_available_to_promise()
        backorder = delivery_pick.backorder_ids
        self.assertEqual(delivery_pick.carrier_id, self.normal_delivery_carrier)
        self.assertEqual(
            delivery_pick.group_id.carrier_id, self.normal_delivery_carrier
        )
        self.assertEqual(backorder.carrier_id, self.super_fast_carrier)
        self.assertEqual(backorder.group_id.carrier_id, self.super_fast_carrier)

    def test_delivery_add_preferred_carrier_picking_domain(self):
        """
        With a qty of 5 in the sale order and 5 available to promise,
        estimated_shipping_weight is 50, and with a priority of 0, preferred
        carrier must be free
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 5
        )
        delivery_pick = self._create_out_picking(product_qty=[(self.product1, 5)])
        self.assertEqual(delivery_pick.priority, PRIORITY_NORMAL)
        self.assertAlmostEqual(delivery_pick._get_estimated_weight(), 50.0)
        delivery_pick._apply_alternative_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.free_delivery_carrier)

    def test_backorder(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 3
        )
        delivery_pick = self._create_out_picking(
            product_qty=[(self.product1, 3), (self.product2, 3)]
        )
        delivery_pick.move_ids.rule_id.no_backorder_at_release = True
        # Setting rule's no_backorder_at_release to True, so the release doesnt
        # creates a backorder
        # by adding stock to only one of the two products of this picking,
        # only one of the 2 created moves should be released.
        # A backorder should be created.
        delivery_pick.release_available_to_promise()
        self.assertTrue(delivery_pick.backorder_id)
