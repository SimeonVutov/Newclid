Geometry cache indexes
======================

``LazyGeometryCache`` builds its data from the points of one problem.
The same endpoints can describe a segment with a length or a line with
a direction. Both indexes refer to one shared list of point pairs.
Each index is built the first time a provider needs that information.

.. _yuclid-point-pairs:

Point pairs
-----------

The cache lists every pair of distinct point indices once. It lists
all pairs starting with index 0, then those starting with index 1,
and so on. Within each group the second index increases. A
``PointPairId`` is the pair's position in this list.

For ``a = (0, 0)``, ``m = (1, 0)``, and ``b = (2, 0)``, suppose
their point indices are 0, 1, and 2.

.. list-table::
   :header-rows: 1

   * - Pair ID
     - Point indices
     - Endpoints
     - Distance
   * - 0
     - ``(0, 1)``
     - ``a, m``
     - 1
   * - 1
     - ``(0, 2)``
     - ``a, b``
     - 2
   * - 2
     - ``(1, 2)``
     - ``m, b``
     - 1

To look up a pair without scanning the list, put its indices in
increasing order. For indices :math:`i < j`, count the pairs in groups
before :math:`i` and add :math:`j-i-1`, the offset within group :math:`i`.
For :math:`n` points, the number of pairs before group :math:`i` is the
total number of pairs minus the number formed by the last :math:`n-i`
points. This is how ``segment_length_bucket_for_pair`` computes the ID.
The lookup returns no bucket for equal indices or indices outside the
problem.

.. _yuclid-segment-length-index:

Segment-length index
--------------------

If a provider already knows one segment, it needs a group of plausible
partners. Sorting pairs by length puts those partners near one another.
The cache computes the distance for each pair and sorts the IDs by
distance. For adjacent lengths :math:`s \le t`, the cache keeps them in
the same bucket when :math:`t-s < \max(10^{-7}, 10^{-3}t)`. The absolute
tolerance covers very small gaps, and the relative tolerance scales
with the length.

Each bucket stores pair IDs. A reverse lookup maps each pair ID to its
bucket index. Whenever a gap fails the tolerance check, the cache closes
the current bucket and starts another. Groups with only one pair are
omitted, so the reverse lookup marks them as having no bucket.

In the example, IDs 0 and 2 go in the length-1 bucket and ID 1 has no
bucket. The reverse lookup takes the provider straight from a known
segment to its plausible partners.

A length bucket grows one neighbor at a time. Lengths 100, 100.09,
and 100.18 can share a bucket because each adjacent gap is small
enough. The first and last lengths differ too much for ``cong``, so
the matcher still needs to check the two segments it will use.

.. _yuclid-line-orientation-index:

Line-orientation index
----------------------

A line's direction is independent of the distance between its endpoints.
Horizontal segments of different lengths can therefore share an
orientation bucket. The cache
uses ``SlopeAngle`` to compute ``atan2(dy, dx)`` from the difference
between the endpoint coordinates. It divides by π and uses
``AddCircle<double>`` to wrap the result into ``[0, 1)``. This expresses
the direction as a fraction of a half-turn. Reversing the endpoints
gives the same orientation.

The cache sorts pair IDs by orientation key and groups neighbors
whose keys differ by less than ``EPS`` (10⁻⁷). The grouping scans the
sorted list from start to end, so it leaves the first and last buckets
separate even if their directions are close across the wraparound.
Each bucket stores its first key and a
half-open range into the sorted ID list. Singleton buckets are retained.
For the points in the table, the three pairs are horizontal and belong to
the same orientation bucket.

The current custom-rule matcher uses the fallback provider for
``para`` and ``perp``. Those predicates do not request this index.

The indexes are built in ``yuclid/src/matchers/lazy_geometry_cache.cpp``.
