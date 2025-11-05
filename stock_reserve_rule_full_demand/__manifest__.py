# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Reserve Rule Full Demand",
    "summary": """This module enhances `stock_reserve_rule` module
    in order to reserve only if the available quantity fullfill the demand""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["rousseldenis"],
    "website": "https://github.com/OCA/stock-logistics-reservation",
    "depends": ["stock_reserve_rule"],
    "data": ["views/stock_removal_strategy.xml"],
}
