# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _get_putaway_child_location(
        self,
        product,
        quantity=0,
        package=None,
        packaging=None,
        additional_qty=None,
    ):
        putaway = self.env["stock.putaway.rule"].search(
            [("product_id", "=", product.id), ("location_in_id", "child_of", self.id)],
            limit=1,
        )
        # TODO: Find a way to retrieve that value (as there is no hook there in Odoo)
        qty_by_location = defaultdict(lambda: 0)
        location = putaway._get_putaway_location(
            product,
            quantity=quantity,
            package=package,
            packaging=packaging,
            qty_by_location=qty_by_location,
        )
        return location if location else self

    def _putaway_strategy_finalizer(
        self,
        putaway_location,
        product,
        quantity=0,
        package=None,
        packaging=None,
        additional_qty=None,
    ):
        if not self.putaway_rule_ids and self.env.context.get(
            "allow_putaway_child_location"
        ):
            putaway_location = self._get_putaway_child_location(
                product,
                quantity=0,
                package=None,
                packaging=None,
                additional_qty=None,
            )
        return super()._putaway_strategy_finalizer(
            putaway_location,
            product,
            quantity=0,
            package=None,
            packaging=None,
            additional_qty=None,
        )
