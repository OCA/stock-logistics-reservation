
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/stock-logistics-reservation&target_branch=18.0)
[![Pre-commit Status](https://github.com/OCA/stock-logistics-reservation/actions/workflows/pre-commit.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-reservation/actions/workflows/pre-commit.yml?query=branch%3A18.0)
[![Build Status](https://github.com/OCA/stock-logistics-reservation/actions/workflows/test.yml/badge.svg?branch=18.0)](https://github.com/OCA/stock-logistics-reservation/actions/workflows/test.yml?query=branch%3A18.0)
[![codecov](https://codecov.io/gh/OCA/stock-logistics-reservation/branch/18.0/graph/badge.svg)](https://codecov.io/gh/OCA/stock-logistics-reservation)
[![Translation Status](https://translation.odoo-community.org/widgets/stock-logistics-reservation-18-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/stock-logistics-reservation-18-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# Stock Reservation

Enhance the way products are allocated (virtual reservation) and reserved (rules extending fifo) in the stock.

Are you looking for modules related to logistics? Or would like to contribute
to? There are many repositories with specific purposes. Have a look at this
[README](https://github.com/OCA/wms/blob/18.0/README.md).

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[sale_stock_available_to_promise_release](sale_stock_available_to_promise_release/) | 18.0.2.0.0 |  | Integration between Sales and Available to Promise Release
[sale_stock_available_to_promise_release_dropshipping](sale_stock_available_to_promise_release_dropshipping/) | 18.0.1.0.0 |  | Glue module between sale_stock_available_to_promise_release and stock_dropshipping
[stock_available_to_promise_release](stock_available_to_promise_release/) | 18.0.1.4.1 |  | Release Operations based on available to promise
[stock_available_to_promise_release_carrier_alternative](stock_available_to_promise_release_carrier_alternative/) | 18.0.1.0.0 |  | Advanced selection of preferred shipping methods
[stock_available_to_promise_release_dynamic_routing](stock_available_to_promise_release_dynamic_routing/) | 18.0.1.0.1 | <a href='https://github.com/jbaudoux'><img src='https://github.com/jbaudoux.png' width='32' height='32' style='border-radius:50%;' alt='jbaudoux'/></a> | Glue between moves release and dynamic routing
[stock_available_to_promise_release_exclude_location](stock_available_to_promise_release_exclude_location/) | 18.0.1.0.0 |  | Exclude locations from available stock
[stock_move_auto_assign](stock_move_auto_assign/) | 18.0.1.0.1 |  | Try to reserve moves when goods enter in a location
[stock_reserve_rule](stock_reserve_rule/) | 18.0.1.0.0 |  | Configure reservation rules by location
[stock_rule_reserve_max_quantity](stock_rule_reserve_max_quantity/) | 18.0.1.0.1 | <a href='https://github.com/Shide'><img src='https://github.com/Shide.png' width='32' height='32' style='border-radius:50%;' alt='Shide'/></a> <a href='https://github.com/rafaelbn'><img src='https://github.com/rafaelbn.png' width='32' height='32' style='border-radius:50%;' alt='rafaelbn'/></a> | Allows to reserve max available quantity when a move comes from an stock rule

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
