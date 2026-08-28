# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict

from odoo import models
from odoo.osv import expression


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _group_by_location(self):
        """Return quants grouped by locations

        Group by location, but keeping the order of the quants (if we have more
        than one quant per location, the order is based on the first quant seen
        in the location). Thus, it can be used on a recordset returned by
        _gather.

        The returned format is: [(location, quants)]

        """
        seen = OrderedDict()
        for quant in self:
            location = quant.location_id
            if location in seen:
                seen[location] = seen[location] | quant
            else:
                seen[location] = quant
        return [(loc, quants) for loc, quants in seen.items()]

    def _get_gather_domain(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        domain = super()._get_gather_domain(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )
        if self.env.context.get("exclude_quant_ids"):
            domain = expression.AND(
                [[("id", "not in", self.env.context["exclude_quant_ids"])], domain]
            )
        return domain
