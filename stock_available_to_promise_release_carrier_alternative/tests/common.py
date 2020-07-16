# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.fields import Command

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)

PRIORITY_NORMAL = PROCUREMENT_PRIORITIES[0][0]
PRIORITY_URGENT = PROCUREMENT_PRIORITIES[1][0]


class DeliveryCarrierPreferenceCommon(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.customer = ref("base.res_partner_12")
        cls.setUpClassProduct()
        cls.setUpClassCarrier()

    @classmethod
    def setUpClassProduct(cls):
        cls.product_model = cls.env["product.product"]
        cls.product = cls.product1
        cls.product.weight = 10.0
        cls.product.volume = 10.0
        cls.delivery_product = cls.env.ref("delivery.product_product_delivery")

    @classmethod
    def setUpClassCarrier(cls):
        cls.carrier_model = cls.env["delivery.carrier"]
        cls.normal_delivery_carrier = cls.carrier_model.create(
            {
                "name": "Normal Carrier",
                "product_id": cls.delivery_product.id,
                "sequence": 10,
                "max_weight": 20,
            }
        )
        cls.the_poste_carrier = cls.carrier_model.create(
            {
                "name": "Poste Carrier",
                "product_id": cls.delivery_product.id,
                "sequence": 20,
                "max_weight": 40,
            }
        )
        cls.super_fast_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Super fast carrier",
                "product_id": cls.delivery_product.id,
                "sequence": 30,
                "picking_domain": f"[('priority', '=', '{PRIORITY_URGENT}')]",
            }
        )
        cls.free_delivery_carrier = cls.carrier_model.create(
            {
                "name": "Free Carrier",
                "product_id": cls.delivery_product.id,
                "sequence": 40,
            }
        )
        cls.normal_delivery_carrier.alternative_carrier_ids = [
            Command.set(
                (
                    cls.the_poste_carrier
                    | cls.super_fast_carrier
                    | cls.free_delivery_carrier
                ).ids
            )
        ]
        cls.the_poste_carrier.alternative_carrier_ids = [
            Command.set(
                (
                    cls.normal_delivery_carrier
                    | cls.super_fast_carrier
                    | cls.free_delivery_carrier
                ).ids
            )
        ]
        cls.super_fast_carrier.alternative_carrier_ids = [
            Command.set(
                (
                    cls.normal_delivery_carrier
                    | cls.the_poste_carrier
                    | cls.free_delivery_carrier
                ).ids
            )
        ]
        cls.free_delivery_carrier.alternative_carrier_ids = [
            Command.set(
                (
                    cls.normal_delivery_carrier
                    | cls.the_poste_carrier
                    | cls.super_fast_carrier
                ).ids
            )
        ]
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
            }
        )
        cls.outgoing_pick_type = cls.wh.out_type_id

    @classmethod
    def _create_out_picking(cls, product_qty=None, carrier=None):
        if not product_qty:
            product_qty = [(cls.product, 2.0)]
        pickings = cls._create_picking_chain(cls.wh, product_qty)
        if not carrier:
            # set the carrier with the highest sequence here
            carrier = cls.free_delivery_carrier
        pickings.write({"carrier_id": carrier.id})
        return pickings
