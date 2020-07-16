# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models
from odoo.tools.safe_eval import const_eval

ALTERNATIVE_CARRIER_IDS_HELP = """
    Change delivery to one of those alternative carriers if the conditions are met.
    Evaluated carriers are this carrier and those alternatives sorted by sequence.
    The first valid carrier will be selected
"""


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    alternative_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        relation="carrier_alternative_carrier_rel",
        column1="carrier_id",
        column2="alternative_id",
        help=ALTERNATIVE_CARRIER_IDS_HELP,
    )
    picking_domain = fields.Char(
        default="[]",
        help="Domain to restrict application of this preference "
        "for carrier selection on pickings",
    )

    def _match_picking(self, picking):
        res = super()._match_picking(picking)
        if domain := const_eval(self.picking_domain):
            return res and bool(picking.filtered_domain(domain))
        return res
