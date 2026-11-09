# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestStockMoveIncreaseFromOrigin(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Models
        cls.Lot = cls.env["stock.lot"]
        cls.Picking = cls.env["stock.picking"]
        cls.Quant = cls.env["stock.quant"]
        # Existing instances
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")
        # Instances
        cls.product = cls.env["product.product"].create(
            {"name": "Lot Tracked Product", "is_storable": True, "tracking": "lot"}
        )
        cls.lot_1 = cls._create_lot("LOT-1")
        cls.lot_2 = cls._create_lot("LOT-2")
        cls.lot_3 = cls._create_lot("LOT-3")
        cls.staging_location = cls.env["stock.location"].create(
            {
                "name": "Staging",
                "usage": "internal",
                "location_id": cls.warehouse.view_location_id.id,
            }
        )
        # Setup
        for lot in cls.lot_1 | cls.lot_2 | cls.lot_3:
            cls.Quant._update_available_quantity(
                cls.product, cls.stock_location, 100.0, lot_id=lot
            )

    @classmethod
    def _create_lot(cls, name, **kwargs):
        return cls.Lot.create({"name": name, "product_id": cls.product.id, **kwargs})

    @classmethod
    def _create_picking(cls, picking_type, location, location_dest, **move_vals):
        return cls.Picking.create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": 10.0,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": location.id,
                            "location_dest_id": location_dest.id,
                            **move_vals,
                        }
                    )
                ],
            }
        )

    @classmethod
    def _create_chain(cls, **move_vals):
        first = cls._create_picking(
            cls.warehouse.int_type_id,
            cls.stock_location,
            cls.staging_location,
            **move_vals,
        )
        second = cls._create_picking(
            cls.warehouse.out_type_id,
            cls.staging_location,
            cls.customer_location,
            procure_method="make_to_order",
            move_orig_ids=[Command.link(first.move_ids.id)],
            **move_vals,
        )
        (first | second).action_confirm()
        return first, second

    def _ship(self, picking, quantities):
        move = picking.move_ids
        move.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            [
                {
                    "move_id": move.id,
                    "picking_id": picking.id,
                    "product_id": move.product_id.id,
                    "lot_id": lot.id,
                    "quantity": quantity,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                }
                for lot, quantity in quantities.items()
            ]
        )
        move.write({"picked": True})
        picking.button_validate()

    def _reserved(self, picking):
        reserved = {}
        for line in picking.move_ids.move_line_ids:
            reserved[line.lot_id] = reserved.get(line.lot_id, 0.0) + line.quantity
        return reserved

    def _free_quantity(self, lot):
        return self.Quant._get_available_quantity(
            self.product, self.staging_location, lot_id=lot, strict=True
        )

    def test_increase_takes_origin_surplus(self):
        first, second = self._create_chain()
        self._ship(first, {self.lot_1: 8.0, self.lot_2: 7.0, self.lot_3: 3.0})
        other_first, other_second = self._create_chain()
        self._ship(other_first, {self.lot_1: 12.0})
        self.assertEqual(self._reserved(second), {self.lot_1: 8.0, self.lot_2: 2.0})
        second.move_ids.write({"quantity": 12.0})
        self.assertEqual(self._reserved(second), {self.lot_1: 8.0, self.lot_2: 4.0})
        self.assertEqual(self._reserved(other_second), {self.lot_1: 10.0})
        self.assertEqual(self._free_quantity(self.lot_1), 2.0)

    def test_increase_beyond_origin_surplus(self):
        first, second = self._create_chain()
        self._ship(first, {self.lot_1: 8.0, self.lot_2: 3.0})
        other_first, other_second = self._create_chain()
        self._ship(other_first, {self.lot_1: 12.0})
        second.move_ids.write({"quantity": 12.0})
        self.assertEqual(self._reserved(second), {self.lot_1: 9.0, self.lot_2: 3.0})
        self.assertEqual(self._reserved(other_second), {self.lot_1: 10.0})

    def test_same_quantity_keeps_reservation(self):
        first, second = self._create_chain()
        self._ship(first, {self.lot_1: 6.0, self.lot_2: 6.0})
        other_first, other_second = self._create_chain()
        self._ship(other_first, {self.lot_1: 12.0})
        second.move_ids._set_quantity_done(10.0)
        self.assertEqual(self._reserved(second), {self.lot_1: 6.0, self.lot_2: 4.0})
        self.assertEqual(self._reserved(other_second), {self.lot_1: 10.0})
        self.assertEqual(self._free_quantity(self.lot_1), 2.0)

    def test_onchange_does_not_reserve(self):
        first, second = self._create_chain()
        self._ship(first, {self.lot_1: 8.0, self.lot_2: 2.0, self.lot_3: 2.0})
        self.assertEqual(self._reserved(second), {self.lot_1: 8.0, self.lot_2: 2.0})
        move = second.move_ids.new(origin=second.move_ids)
        move._set_quantity_done(12.0)
        self.assertEqual(sum(move.move_line_ids.mapped("quantity")), 12.0)
        move._set_quantity_done(6.0)
        self.assertEqual(sum(move.move_line_ids.mapped("quantity")), 6.0)
        self.assertEqual(self._reserved(second), {self.lot_1: 8.0, self.lot_2: 2.0})
        self.assertEqual(self._free_quantity(self.lot_3), 2.0)
        self.assertFalse(
            self.env["stock.move.line"].search(
                [("product_id", "=", self.product.id), ("move_id", "=", False)]
            )
        )

    def test_decrease_releases_last_reserved(self):
        first, second = self._create_chain()
        self._ship(first, {self.lot_1: 4.0, self.lot_2: 8.0})
        other_first, other_second = self._create_chain()
        self._ship(other_first, {self.lot_1: 12.0})
        self.assertEqual(self._reserved(second), {self.lot_1: 4.0, self.lot_2: 6.0})
        second.move_ids._set_quantity_done(6.0)
        self.assertEqual(self._reserved(second), {self.lot_1: 4.0, self.lot_2: 2.0})
        self.assertEqual(self._reserved(other_second), {self.lot_1: 10.0})
        self.assertEqual(self._free_quantity(self.lot_1), 2.0)
        second.move_ids._set_quantity_done(3.0)
        self.assertEqual(self._reserved(second), {self.lot_1: 3.0})
        second.move_ids._set_quantity_done(0.0)
        self.assertFalse(second.move_ids.move_line_ids)

    def test_other_unit_of_measure(self):
        other_first, other_second = self._create_chain()
        self._ship(other_first, {self.lot_1: 16.0})
        first, second = self._create_chain(
            product_uom=self.dozen.id, product_uom_qty=3.0
        )
        self._ship(first, {self.lot_1: 1.0, self.lot_2: 2.5})
        self.assertEqual(second.move_ids.move_line_ids.product_uom_id, self.dozen)
        self.assertEqual(self._reserved(second), {self.lot_1: 1.0, self.lot_2: 2.0})
        second.move_ids._set_quantity_done(3.5)
        self.assertEqual(self._reserved(second), {self.lot_1: 1.0, self.lot_2: 2.5})
        second.move_ids._set_quantity_done(2.5)
        self.assertEqual(self._reserved(second), {self.lot_1: 1.0, self.lot_2: 1.5})
        self.assertEqual(self._reserved(other_second), {self.lot_1: 10.0})
        self.assertEqual(self._free_quantity(self.lot_1), 6.0)

    def test_serial_numbers(self):
        product = self.env["product.product"].create(
            {"name": "Serial Product", "is_storable": True, "tracking": "serial"}
        )
        serials = [
            self._create_lot(f"SN-{index}", product_id=product.id)
            for index in range(1, 7)
        ]
        for serial in serials:
            self.Quant._update_available_quantity(
                product, self.stock_location, 1.0, lot_id=serial
            )
        other_first, other_second = self._create_chain(
            product_id=product.id, product_uom_qty=1.0
        )
        self._ship(other_first, {serials[4]: 1.0, serials[5]: 1.0})
        first, second = self._create_chain(product_id=product.id, product_uom_qty=3.0)
        self._ship(first, {serial: 1.0 for serial in serials[:4]})
        second.move_ids._set_quantity_done(4.0)
        self.assertEqual(
            self._reserved(second), {serial: 1.0 for serial in serials[:4]}
        )
        second.move_ids._set_quantity_done(2.0)
        self.assertEqual(
            self._reserved(second), {serial: 1.0 for serial in serials[:2]}
        )
        self.assertEqual(self._reserved(other_second), {serials[4]: 1.0})

    def test_increase_without_origin_keeps_standard_behavior(self):
        picking = self._create_picking(
            self.warehouse.int_type_id, self.stock_location, self.staging_location
        )
        picking.action_confirm()
        self.assertEqual(self._reserved(picking), {self.lot_1: 10.0})
        picking.move_ids.write({"quantity": 12.0})
        self.assertEqual(self._reserved(picking), {self.lot_1: 12.0})
