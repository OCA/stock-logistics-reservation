There is nothing to configure. For example, with two chained transfers of 10
units:

1. The first transfer brings 8 units of lot A and 7 units of lot B to the next
   location.
2. The second transfer reserves 8 units of lot A and 2 units of lot B.
3. Another transfer left 2 free units of lot A in the same location.
4. Set the quantity of the second transfer to 12: the 2 extra units come from
   lot B, which its origin brought, instead of the free units of lot A.

In a manufacturing order whose components come from a done transfer, setting a
quantity to produce below the planned one only releases the last reserved lots
of the components.
