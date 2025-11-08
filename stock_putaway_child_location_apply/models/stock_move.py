# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        moves_apply_putaway_child_ids = self.filtered(
            lambda move: move.picking_id.picking_type_id.allow_to_apply_child_putaway
        )
        if moves_apply_putaway_child_ids:
            moves_apply_putaway_child_ids = moves_apply_putaway_child_ids.with_context(
                allow_putaway_child_location=True
            )
            super(StockMove, moves_apply_putaway_child_ids)._action_assign(
                force_qty=force_qty
            )
        return super(StockMove, (self - moves_apply_putaway_child_ids))._action_assign(
            force_qty=force_qty
        )
