Congruence provider
===================

``cong A B C D`` asks whether segments ``AB`` and ``CD`` have equal
length. ``CongProvider`` uses whatever the matcher already knows about
those segments to narrow the search. A complete segment gives it a
length to look up. A single known endpoint gives it a point the segment
has to touch.

Choosing segments from buckets
------------------------------

Generation uses the :ref:`segment-length index <yuclid-segment-length-index>`.
An endpoint that already has a point is an *anchor*. Two known endpoints
on the same segment give the provider an exact pair to look up. One
endpoint on each segment tells it where both segments must touch, but it
still has to look through buckets to find possible lengths.

.. list-table::
   :header-rows: 1
   :widths: 30 16 54

   * - What is known
     - Example mask
     - How the provider extends the mapping
   * - No endpoints
     - ``0000``
     - Try ordered pairs of segments within each bucket. For each pair,
       try both endpoint orders of each segment, giving four
       orientations to check against the variable pattern.
   * - One endpoint
     - ``1000``
     - In each bucket, find a segment touching the anchor. Pair it with
       a different segment in that bucket and try both orders for the
       unanchored segment.
   * - One endpoint per segment
     - ``1010``
     - In each bucket, find two different segments. Each must touch
       its own anchor. The other endpoints supply the missing points.
   * - One whole segment
     - ``1100``
     - Look up the known segment's bucket. Try the available segments
       in that bucket in both endpoint orders.
   * - One whole segment and an anchor
     - ``1110``
     - Look up the known segment's bucket. For each segment that touches
       the other side's anchor, try its free endpoint.
   * - Both whole segments
     - ``1111``
     - All positions already have points, so there is no extension to yield.

The masks in the table show one arrangement per case. The provider also
handles the corresponding cases with the other endpoints assigned.

When trying candidate endpoints, the provider skips points already used
by the mapping unless they are the anchors being reused. When it proposes
points for two argument positions, those points must coincide exactly
when the positions name the same variable. This allows the two segments
in ``cong A M M B`` to share ``M`` while keeping distinct rule variables
on distinct points.

For ``cong A B A B`` and ``cong A B B A``, the two sides describe the
same segment. The provider bypasses buckets, including when a segment
has no bucket. If neither variable is assigned, it yields both orders
of each unused point pair. If one variable is assigned, it tries every
unused point for the other.

Finding the missing endpoint
----------------------------

Suppose ``cong A M M B`` has ``A → a`` and ``M → m``. The first
segment is already ``am``. The other segment must touch ``m``, so
only its other endpoint is missing.

1. ``segment_length_bucket_for_pair`` computes the pair ID for ``am``
   and finds the bucket through the reverse lookup. In the
   :ref:`worked cache example <yuclid-point-pairs>`, that is pair ID 0
   and the bucket contains IDs 0 and 2.
2. Both pairs touch ``m``. Pair 0 would assign ``a`` to ``B``, but
   ``A`` already uses that point. Pair 2 has ``b`` as its free endpoint.
3. The provider yields ``B → b``. With both segments assigned, the
   matcher can check whether their lengths agree.

Checking the actual lengths
---------------------------

Bucket membership suggests candidates. A bucket can contain lengths
that are too far apart to satisfy ``cong``. Once all positions are
assigned, ``is_satisfied`` builds a ``DistEqDist`` statement and checks
both segments for non-degeneracy. It then compares their lengths using
the absolute and relative tolerances from the
:ref:`segment-length index <yuclid-segment-length-index>`. The check uses
the lengths of the two assigned segments directly. It returns false
when any argument position still lacks a point.

Reading the four argument positions
-----------------------------------

The provider gives each distinct variable a local index in order of first
appearance. For ``cong A M M B``, the four positions have local indices
``[0, 1, 1, 2]``. These indices refer to the planned predicate's variable
list. The provider follows that list into the current mapping to get
the point, if any, assigned to each position.

It then sets one bit per assigned position, reading left to right from
the highest bit. With ``A → a`` and ``M → m``, the position list is
``[a, m, m, unassigned]``. The mask is ``1110`` even though only two
distinct variables have points. That mask tells the provider it knows a
whole segment and an endpoint of the other segment.

Estimating the work
-------------------

A known length can limit the search to one bucket. A known endpoint
can narrow it further. The estimate reflects those differences so the
matcher can prefer a predicate likely to produce fewer extensions.

Let ``N``
be the number of problem points, ``K`` the number of length buckets,
and ``S`` the total number of point pairs divided by ``K`` and rounded
down. The total includes pairs with no bucket. When ``K`` is zero,
the provider uses zero for ``S``.

Before adding the predicate's base cost, the provider calculates:

- **Nothing assigned.** Use ``4 × K × S²`` to approximate the ordered
  segment pairs and their four endpoint orders.
- **One endpoint assigned.** Use ``2 × (N − 1) × S`` when the problem
  has points, allowing two orders for the unanchored segment.
- **One endpoint per segment.** Start with the one-endpoint estimate,
  divide by ``N``, round up, and use at least 1 when ``N > 0``.
- **A whole segment assigned.** Use twice the number of other segments
  in its bucket, or zero if it has no bucket. If the other segment has
  an anchor, divide by ``N``, round up, and use at least 1 when there is
  a bucket and ``N > 0``.
- **All endpoints assigned.** Use zero.

These are search-order estimates. They use the binding mask even for
identity patterns, whose generation takes the separate path above.

The implementation is in ``yuclid/src/matchers/cong_provider.cpp``.
