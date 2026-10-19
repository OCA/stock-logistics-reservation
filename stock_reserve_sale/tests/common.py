# © 2023 FactorLibre - Hugo Córdoba <hugo.cordoba@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon


class TestStockReserveSaleCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner", "country_id": cls.env.ref("base.es").id}
        )
        cls.warehouse = cls.env["stock.warehouse"].create(
            {"name": "Test warehouse", "code": "TEST"}
        )
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "is_storable": True}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "is_storable": True}
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product_1.id,
                "location_id": cls.warehouse.lot_stock_id.id,
                "quantity": 10.0,
            }
        )
        cls.env["stock.quant"].create(
            {
                "product_id": cls.product_2.id,
                "location_id": cls.warehouse.lot_stock_id.id,
                "quantity": 10.0,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product_1.id,
                            "product_uom_qty": 1,
                            "price_unit": 6.7,
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.product_1.id,
                            "product_uom_qty": 1,
                            "price_unit": 6.7,
                        }
                    ),
                ],
            }
        )
        cls.sale_order_2 = cls.sale_order.copy()
