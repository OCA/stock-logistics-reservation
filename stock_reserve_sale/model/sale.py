# Copyright 2013 Camptocamp SA - Guewen Baconnier
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools.translate import _

_LINE_KEYS = ["product_id", "product_uom_qty"]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "state", "order_line.reservation_ids", "order_line.is_stock_reservable"
    )
    def _compute_stock_reservation(self):
        for sale in self:
            has_stock_reservation = False
            is_stock_reservable = False
            for line in sale.order_line:
                if line.reservation_ids:
                    has_stock_reservation = True
                if line.is_stock_reservable:
                    is_stock_reservable = True
            if sale.state not in ("draft", "sent"):
                is_stock_reservable = False
            sale.is_stock_reservable = is_stock_reservable
            sale.has_stock_reservation = has_stock_reservation

    has_stock_reservation = fields.Boolean(
        compute="_compute_stock_reservation",
        readonly=True,
        store=True,
        string="Has Stock Reservations",
    )
    is_stock_reservable = fields.Boolean(
        compute="_compute_stock_reservation",
        readonly=True,
        store=True,
        string="Can Have Stock Reservations",
    )
    reserves_count = fields.Integer(
        compute="_compute_reserves_count",
        store=True,
        compute_sudo=False,
    )
    all_lines_reserved = fields.Boolean(
        compute="_compute_reserves_count",
        store=True,
        default=False,
        compute_sudo=False,
    )
    stock_reservation_ids = fields.One2many(
        "stock.reservation", "sale_id", string="Stock Reservations"
    )

    def release_all_stock_reservation(self):
        self.order_line.release_stock_reservation()
        return True

    def action_open_release_reservation_wizard(self):
        self.ensure_one()
        wizard = self.env["sale.stock.reserve.release"].create(
            {
                "sale_order_id": self.id,
                "reservation_ids": [
                    Command.set(
                        self.stock_reservation_ids.filtered(
                            lambda r: r.state != "cancel"
                        ).ids
                    )
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.stock.reserve.release",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.depends("stock_reservation_ids", "order_line.product_id.type")
    def _compute_reserves_count(self):
        for order in self:
            lines = order.order_line.filtered(
                lambda ln: ln.product_id.type != "service"
            )
            reserves_count = len(order.stock_reservation_ids)
            order.reserves_count = reserves_count
            order.all_lines_reserved = bool(reserves_count == len(lines))

    def action_view_reserves_products(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_reserve.action_stock_reservation_tree"
        )
        action["domain"] = [("sale_id", "in", self.ids)]
        action["context"] = {"search_default_groupby_product": False}
        return action

    def action_confirm(self):
        self.release_all_stock_reservation()
        return super().action_confirm()

    def action_cancel(self):
        self.release_all_stock_reservation()
        return super().action_cancel()

    def write(self, vals):
        dict_old_lines = {
            line.id: {
                "product_id": line.product_id,
                "product_uom_qty": line.product_uom_qty,
            }
            for line in self.order_line
        }
        res = super().write(vals)
        for order in self:
            body = ""
            for command in vals.get("order_line", []):
                if command[0] == Command.UPDATE and set(command[2]).intersection(
                    _LINE_KEYS
                ):
                    body += order.get_message(
                        dict_old_lines.get(command[1]), command[2]
                    )
            if body:
                order.message_post(body=body)
        return res

    @api.model
    def get_message(self, old_vals, new_vals):
        ProductProduct = self.env["product.product"]
        body = _("<p>Modified Order line data</p>")
        if "product_id" in new_vals:
            old_product = old_vals["product_id"].display_name
            new_product = ProductProduct.browse(new_vals["product_id"]).display_name
            body += _("<div>     <b>Product</b>: ")
            body += f"{old_product} → {new_product}</div>"
        if "product_uom_qty" in new_vals:
            if "product_id" not in new_vals:
                body += _("<div>     <b>Product</b>: %s") % (
                    old_vals["product_id"].display_name
                )
            body += _("<div>     <b>Product qty.</b>: ")
            body += "{} → {}</div>".format(
                old_vals["product_uom_qty"],
                float(new_vals["product_uom_qty"]),
            )
        body += "<br/>"
        return body

    def unlink(self):
        for order in self:
            if order.has_stock_reservation:
                raise UserError(
                    _(
                        "Sale Order %(order_name)s has some reserved lines.\n"
                        "Please unreserve these lines before deleting the order.",
                        order_name=order.name,
                    )
                )
        return super().unlink()
