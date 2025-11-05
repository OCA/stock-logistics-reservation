# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_compare


class StockReserveRuleRemoval(models.Model):
    _inherit = "stock.reserve.rule.removal"

    removal_strategy = fields.Selection(
        selection_add=[("full_demand", "Full Demand")],
        ondelete={"full_demand": "set default"},
    )

    full_demand_fallback_location_ids = fields.Many2many(
        comodel_name="stock.location",
        relation="stock_reserve_rule_removal_stock_location_rel",
        column1="rule_id",
        column2="location_id",
        string="Full Demand Fallback Locations",
        help="This is the locations where to check if products"
        " are available to enable or not the full demand rule."
        " Don't fill in this if you don't want fallback.",
    )

    def _filter_quants(self, move, quants):
        """
        If the rule is "Full Demand" and if the available quantity
        is lower than the move demand, returns a void quant recordset.
        """
        quants = super()._filter_quants(move, quants)
        if self.removal_strategy == "full_demand":
            if self.full_demand_fallback_location_ids:
                qty = sum(
                    [
                        move.product_id.with_context(
                            location=location.id
                        ).virtual_available
                        for location in self.full_demand_fallback_location_ids
                    ]
                )
                if (
                    float_compare(
                        qty,
                        move.product_uom_qty,
                        precision_rounding=move.product_id.uom_id.rounding,
                    )
                    > 0
                ):
                    return quants.browse()

            if (
                float_compare(
                    sum(quant.available_quantity for quant in quants),
                    move.product_uom_qty,
                    precision_rounding=move.product_id.uom_id.rounding,
                )
                < 0
            ):
                return quants.browse()
        return quants

    def _apply_strategy_full_demand(self, quants):
        """
        This won't be triggered if no quants have been returned by
        the filter function.
        So, for other cases, returns the default strategy.
        """
        return self._apply_strategy_default(quants)
