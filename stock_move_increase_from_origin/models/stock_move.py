# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    def _set_quantity_done(self, qty):
        to_set_moves = self
        for move in self:
            if move._set_quantity_done_from_origin(qty):
                to_set_moves -= move
        if not to_set_moves:
            return None
        return super(StockMove, to_set_moves)._set_quantity_done(qty)

    def _set_quantity_done_from_origin(self, qty):
        self.ensure_one()
        if (
            isinstance(self.id, models.NewId)
            or self.state == "done"
            or self._should_bypass_reservation()
            or not any(origin.state == "done" for origin in self.move_orig_ids)
        ):
            return False
        rounding = self.product_id.uom_id.rounding
        need = self.product_uom._compute_quantity(
            qty, self.product_id.uom_id, round=False
        ) - sum(self.move_line_ids.mapped("quantity_product_uom"))
        if float_compare(need, 0, precision_rounding=rounding) < 0:
            self._release_reserved_quantity(-need)
            return True
        if float_is_zero(need, precision_rounding=rounding):
            return True
        move_lines = self.move_line_ids
        need -= self._reserve_from_origin(need)
        if float_compare(need, 0, precision_rounding=rounding) > 0:
            need -= self._update_reserved_quantity(
                need,
                self.location_id,
                package_id=self.package_level_id.package_id or None,
                strict=False,
            )
        (self.move_line_ids - move_lines)._apply_putaway_strategy()
        return float_compare(need, 0, precision_rounding=rounding) <= 0

    def _reserve_from_origin(self, need):
        rounding = self.product_id.uom_id.rounding
        available = self._get_available_move_lines(set(), set())
        taken = 0.0
        for (location, lot, package, owner), quantity in available.items():
            missing = need - taken
            if float_compare(missing, 0, precision_rounding=rounding) <= 0:
                break
            taken += self._update_reserved_quantity(
                min(quantity, missing),
                location,
                lot_id=lot,
                package_id=package,
                owner_id=owner,
            )
        return taken

    def _release_reserved_quantity(self, quantity):
        rounding = self.product_id.uom_id.rounding
        lines = self.move_line_ids.filtered(
            lambda line: float_compare(
                line.quantity_product_uom, 0, precision_rounding=rounding
            )
            > 0
        )
        to_unlink = self.env["stock.move.line"]
        for line in lines.sorted("id", reverse=True):
            if float_compare(quantity, 0, precision_rounding=rounding) <= 0:
                break
            line_quantity = line.quantity_product_uom
            if float_compare(line_quantity, quantity, precision_rounding=rounding) <= 0:
                to_unlink |= line
                quantity -= line_quantity
                continue
            line.write(
                {
                    "quantity": self.product_id.uom_id._compute_quantity(
                        line_quantity - quantity, line.product_uom_id, round=False
                    )
                }
            )
            quantity = 0
        to_unlink.unlink()
