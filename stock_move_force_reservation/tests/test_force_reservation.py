# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Mathieu Delva <mathieu.delva@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ast import literal_eval

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestForceReservation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.product = cls.env["product.product"].create(
            {
                "name": "TEST PRODUCT",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.partner_id = cls.env.ref("base.res_partner_2")
        cls.picking_type_id = cls.env.ref("stock.picking_type_out")
        cls.location_id = cls.env.ref("stock.stock_location_stock")
        cls.location_dest_id = cls.env.ref("stock.stock_location_customers")
        cls.product_uom = cls.env.ref("uom.product_uom_unit")

    @classmethod
    def _create_picking(cls, name, **move_vals):
        vals = {
            "name": name,
            "product_id": cls.product.id,
            "product_uom": cls.product_uom.id,
            "product_uom_qty": 1,
            **move_vals,
        }

        picking = cls.env["stock.picking"].create(
            {
                "name": name,
                "partner_id": cls.partner_id.id,
                "picking_type_id": cls.picking_type_id.id,
                "location_id": cls.location_id.id,
                "location_dest_id": cls.location_dest_id.id,
                "move_ids_without_package": [
                    Command.create(vals),
                ],
            }
        )
        picking.action_confirm()

        return picking

    @classmethod
    def _create_move(cls, name, **move_vals):
        picking = cls._create_picking(name, **move_vals)
        return picking, picking.move_ids_without_package

    def test_force_availability(self):
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "quantity": 1,
            }
        )

        picking, source_move = self._create_move("Pick1")
        picking.action_assign()

        picking2, target_move = self._create_move("Pick2")

        source_move._compute_qty_in_stock()

        self.assertEqual(source_move.qty_in_stock, 1)
        self.assertEqual(picking.state, "assigned")
        self.assertEqual(picking2.state, "confirmed")

        wizard = (
            self.env["stock.move.force.reservation"]
            .with_context(
                active_model="stock.move",
                active_id=target_move.id,
                active_ids=[target_move.id],
            )
            .create(
                {
                    "picking_id": picking2.id,
                    "move_id": target_move.id,
                    "product_id": target_move.product_id.id,
                    "location_id": target_move.location_id.id,
                    "move_to_unreserve_ids": [
                        Command.set(source_move.ids),
                    ],
                }
            )
        )

        self.assertEqual(wizard.total_quantity, 1)

        wizard.validate()

        self.assertEqual(picking.state, "confirmed")
        self.assertEqual(picking2.state, "assigned")

    def test_force_quantity(self):
        _, move = self._create_move("PickTest")

        action = move.force_quantity()

        self.assertEqual(action.get("type"), "ir.actions.act_window")

        context = action.get("context")
        self.assertIsInstance(context, dict)
        self.assertEqual(context.get("active_id"), move.id)
        self.assertEqual(context.get("active_model"), move._name)

    def test_moves_with_ancestors_cannot_be_unreserved(self):
        """Moves with ancestors must be excluded from the unreserve candidates."""
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location_id.id,
                "quantity": 10,
            }
        )

        _, source_move = self._create_move("move_source")

        _, dependent_move = self._create_move(
            "move_dependent",
            move_orig_ids=[Command.link(source_move.id)],
        )

        independent_picking, independent_move = self._create_move("move_independent")
        independent_picking.action_assign()

        self.assertEqual(independent_move.state, "assigned")
        self.assertIn(source_move, dependent_move.move_orig_ids)
        self.assertFalse(independent_move.move_orig_ids)

        with Form(
            self.env["stock.move.force.reservation"].with_context(
                active_model="stock.move",
                active_id=source_move.id,
                active_ids=[source_move.id],
            )
        ) as wizard_form:
            self.assertEqual(wizard_form.move_id, source_move)
            self.assertEqual(wizard_form.product_id, source_move.product_id)
            self.assertEqual(wizard_form.location_id, source_move.location_id)

            domain = literal_eval(wizard_form.move_to_unreserve_ids_domain)

        eligible_moves = self.env["stock.move"].search(domain)

        self.assertNotIn(dependent_move, eligible_moves)
        self.assertIn(independent_move, eligible_moves)
