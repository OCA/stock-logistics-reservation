# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Putaway Child Location Apply",
    "summary": """This module allows to apply in some conditions
    a putaway rule on move destination child location""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reservation",
    "depends": [
        "stock",
        "stock_putaway_hook",
    ],
    "data": ["views/stock_picking_type.xml"],
}
