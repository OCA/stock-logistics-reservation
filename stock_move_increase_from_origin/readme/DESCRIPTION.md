When the quantity of a move goes up, Odoo spreads it over the move lines in
order: each line takes the free stock of its own lot in the location before the
next line is checked, and the next lines are reduced if needed. That free stock
may belong to another chain of transfers. So a chained move can take what
another transfer brought and leave unused what its own origin moves brought. In
a manufacturing order this happens with any quantity to produce, even below the
planned one, because setting it spreads the components again.

With this module, a chained move whose origin moves are done keeps its move
lines and takes the extra quantity from what its origin moves brought, the same
way Odoo reserves it. What they cannot cover is reserved as usual, and only if
there is no stock left Odoo adds a move line without reservation. When the
quantity goes down, the move only releases stock, starting with the last
reserved move lines, as Odoo does when the quantity of a transfer is lowered.
