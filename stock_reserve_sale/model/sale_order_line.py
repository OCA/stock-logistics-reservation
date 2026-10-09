# Copyright 2013 Camptocamp SA - Guewen Baconnier
# Copyright 2023 - Hugo Córdoba - FactorLibre - (hugo.cordoba@factorlibre.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    reservation_ids = fields.One2many(
        "stock.reservation", "sale_line_id", string="Stock Reservation", copy=False
    )
    is_stock_reservable = fields.Boolean(
        compute="_compute_is_stock_reservable", readonly=True, string="Can be reserved"
    )
    is_readonly = fields.Boolean(compute="_compute_is_readonly", store=False)

    @api.depends(
        "state",
        "product_id",
        "product_id.route_ids",
        "product_id.type",
        "is_mto",
        "reservation_ids",
    )
    def _compute_is_stock_reservable(self):
        for line in self:
            reservable = False
            if (
                not (
                    line.state not in ("draft", "sent")
                    or line.is_mto
                    or not line.product_id
                    or line.product_id.type == "service"
                )
                and not line.reservation_ids
            ):
                reservable = True
            line.is_stock_reservable = reservable

    @api.depends("order_id.state", "reservation_ids")
    def _compute_is_readonly(self):
        for line in self:
            line.is_readonly = (
                len(line.reservation_ids) > 0 or line.order_id.state != "draft"
            )

    def release_stock_reservation(self):
        reservations = self.reservation_ids
        reservations.release_reserve()
        return True

    def write(self, vals):
        block_on_reserve = ("product_id", "product_uom_id", "type")
        update_on_reserve = ("price_unit", "product_uom_qty")
        keys = set(vals.keys())
        test_block = keys.intersection(block_on_reserve)
        test_update = keys.intersection(update_on_reserve)
        if test_block:
            for line in self:
                if not line.reservation_ids:
                    continue
                raise UserError(
                    self.env._(
                        "You cannot change the product or unit of measure "
                        "of lines with a stock reservation. "
                        "Release the reservation "
                        "before changing the product."
                    ),
                )
        res = super().write(vals)
        if test_update:
            for line in self:
                if not line.reservation_ids:
                    continue
                if len(line.reservation_ids) > 1:
                    raise UserError(
                        self.env._(
                            "Several stock reservations are linked with the "
                            "line. Impossible to adjust their quantity. "
                            "Please release the reservation "
                            "before changing the quantity."
                        ),
                    )
                line.reservation_ids.write(
                    {
                        "price_unit": line.price_unit,
                        "product_uom_qty": line.product_uom_qty,
                    }
                )
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_reservation(self):
        for line in self:
            if line.reservation_ids:
                raise UserError(
                    self.env._(
                        "Sale order line [%(order_name)s] "
                        "'%(line_name)s' has a related reservation.\n"
                        "Please unreserve this line before deleting it.",
                        order_name=line.order_id.name,
                        line_name=line.name,
                    )
                )
