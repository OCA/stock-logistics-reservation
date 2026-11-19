# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestStockReserve(BaseCommon):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.env["res.config.settings"].create(
            {
                "group_stock_multi_locations": True,
            }
        ).set_values()
        warehouse_form = Form(self.env["stock.warehouse"])
        warehouse_form.name = "Test warehouse"
        warehouse_form.code = "TEST"
        self.warehouse = warehouse_form.save()
        product_form = Form(self.env["product.product"])
        product_form.name = "Test Product"
        product_form.type = "consu"
        product_form.is_storable = True
        self.product = product_form.save()
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": 10.0,
            }
        )

    def _create_stock_reservation(self, qty):
        form_reservation = Form(self.env["stock.reservation"])
        form_reservation.product_id = self.product
        form_reservation.product_uom_qty = qty
        form_reservation.location_id = self.warehouse.lot_stock_id
        return form_reservation.save()

    def test_reservation_and_reservation_release(self):
        reservation_1 = self._create_stock_reservation(6)
        reservation_1.reserve()
        self.assertFalse(reservation_1.picking_id)
        self.assertEqual(self.product.virtual_available, 4)
        reservation_2 = self._create_stock_reservation(1)
        reservation_2.reserve()
        self.assertFalse(reservation_2.picking_id)
        self.assertEqual(self.product.virtual_available, 3)
        reservation_1.release_reserve()
        self.assertEqual(self.product.virtual_available, 9)

    def test_cron_release(self):
        reservation_1 = self._create_stock_reservation(6)
        reservation_1.date_validity = fields.Date.from_string("2021-01-01")
        reservation_1.reserve()
        self.assertFalse(reservation_1.picking_id)
        self.assertEqual(self.product.virtual_available, 4)
        cron = self.env.ref("stock_reserve.ir_cron_release_stock_reservation")
        cron.method_direct_trigger()
        self.assertEqual(self.product.virtual_available, 10)

    def test_cron_reserve(self):
        reservation_1 = self._create_stock_reservation(11)
        reservation_1.reserve()
        self.assertFalse(reservation_1.picking_id)
        self.assertEqual(reservation_1.state, "partially_available")
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": 10.0,
            }
        )
        cron = self.env.ref("stock_reserve.ir_cron_reserve_waiting_confirmed")
        cron.method_direct_trigger()
        self.assertEqual(reservation_1.state, "assigned")
        self.assertEqual(self.product.virtual_available, 9)

    def test_reserve_several_reservations_with_different_uoms(self):
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        product_dozen = self.env["product.product"].create(
            {
                "name": "Test Product in Dozens",
                "type": "consu",
                "is_storable": True,
                "uom_id": uom_dozen.id,
                "uom_po_id": uom_dozen.id,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": product_dozen.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": 10.0,
            }
        )
        reservation_unit = self._create_stock_reservation(6)
        form_reservation = Form(self.env["stock.reservation"])
        form_reservation.product_id = product_dozen
        form_reservation.product_uom_qty = 2
        form_reservation.location_id = self.warehouse.lot_stock_id
        reservation_dozen = form_reservation.save()
        reservations = reservation_unit | reservation_dozen
        self.assertEqual(len(reservations.product_uom), 2)
        reservations.reserve()
        self.assertEqual(reservations.mapped("state"), ["assigned", "assigned"])
        self.assertEqual(self.product.virtual_available, 4)
        self.assertEqual(product_dozen.virtual_available, 8)
        reservations.write({"product_uom_qty": 3})
        self.assertEqual(self.product.virtual_available, 7)
        self.assertEqual(product_dozen.virtual_available, 7)
