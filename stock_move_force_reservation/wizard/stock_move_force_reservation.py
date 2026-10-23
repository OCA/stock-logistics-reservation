# Copyright 2024 Akretion France (http://www.akretion.com/)
# @author: Mathieu Delva <mathieu.delva@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockMoveForceReservation(models.TransientModel):
    _name = "stock.move.force.reservation"
    _description = "stock move force reservation"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Current Transfer",
        readonly=True,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Source Location",
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="stock.move",
        string="Current Move",
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Current Product",
        readonly=True,
    )

    move_to_unreserve_ids_domain = fields.Char(
        compute="_compute_move_to_unreserve_ids_domain",
        readonly=True,
        store=False,
    )

    move_to_unreserve_ids = fields.Many2many(
        comodel_name="stock.move",
        string="Moves To Unreserve",
        help="Moves from other transfers that will be unreserve",
    )
    total_quantity = fields.Float(compute="_compute_total_quantity")

    @api.depends("product_id", "move_id", "location_id")
    def _compute_move_to_unreserve_ids_domain(self):
        for rec in self:
            rec.move_to_unreserve_ids_domain = [
                ("id", "!=", rec.move_id.id),
                ("product_id", "=", rec.product_id.id),
                (
                    "state",
                    "in",
                    ["assigned", "partially_available"],
                ),
                ("location_id", "child_of", rec.location_id.ids),
                ("move_orig_ids", "=", False),
            ]

    @api.model
    def default_get(self, fields_list):
        rec = super().default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        stock_move = self.env["stock.move"].browse(active_id).exists()
        if not stock_move:
            raise UserError(self.env._("No stock move available."))

        rec.update(
            {
                "move_id": stock_move,
                "product_id": stock_move.product_id,
                "picking_id": stock_move.picking_id,
                "location_id": stock_move.picking_id.location_id,
            }
        )
        return rec

    @api.depends("move_to_unreserve_ids")
    def _compute_total_quantity(self):
        total_quantity = 0
        for record in self.move_to_unreserve_ids:
            total_quantity += record.product_uom_qty
        self.total_quantity = total_quantity

    def validate(self):
        moves_to_unreserve = self.move_to_unreserve_ids
        moves_to_unreserve._do_unreserve()
        self.picking_id.action_assign()
        moves_to_unreserve._action_assign()
