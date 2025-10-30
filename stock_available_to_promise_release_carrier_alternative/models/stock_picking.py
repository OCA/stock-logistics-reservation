# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _apply_alternative_carrier(self):
        self.ensure_one()
        carrier = self._get_preferred_carrier()
        if not carrier:
            return False
        if carrier == self.carrier_id:
            return False
        # Set a context key to not trigger a carrier change on the
        # procurement group
        self.with_context(skip_align_group_carrier=True).carrier_id = carrier
        defaults = {
            "carrier_id": carrier.id,
            "name": self.env._(
                "%s - Alternative carrier %s", self.group_id.name, carrier.name
            ),
        }
        self.group_id = self.group_id.copy(default=defaults)
        active_moves = self.move_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
        )
        active_moves.group_id = self.group_id
        # Manage the carrier route, but skip when the route was forced
        if (
            (rerouted_moves := active_moves.filtered(lambda m: not m.route_ids))
            and (routes := carrier.route_ids.filtered("active"))
            and (
                rule := self.env["procurement.group"]._get_rule(
                    self.env["product.product"],
                    self.location_dest_id,
                    {"route_ids": routes},
                )
            )
        ):
            rerouted_moves.write(
                {
                    "location_id": rule.location_src_id.id,
                    "rule_id": rule.id,
                    "picking_type_id": rule.picking_type_id.id,
                    "procure_method": rule.procure_method,
                    "propagate_cancel": rule.propagate_cancel,
                }
            )
            rerouted_moves._unreleased_to_backorder(split_order=True)
            # If all moves are moved to another picking, the initial picking will
            # be draft. Force it to cancel.
            if not self.move_ids:
                self.state = "cancel"
        return True

    def _get_preferred_carrier(self):
        self.ensure_one()
        picking_carrier = self.carrier_id
        # we consider current carrier as well allowing to configure better
        # carriers as alternative or less restrictive carrier as fallback
        possible_carriers = picking_carrier | picking_carrier.alternative_carrier_ids
        for carrier in possible_carriers.sorted("sequence"):
            if carrier._match_picking(self):
                return carrier
