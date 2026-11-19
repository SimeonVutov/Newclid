Base provider
=============

``BaseProvider`` gives the matcher a way to handle any supported
predicate. It tries ways of filling the missing variables with unused
points and checks geometry when the matcher asks. A specialized
provider can use the shape of a predicate to narrow that search.

Suppose ``coll A B C`` already has a point for ``A``. Swapping the
points for ``B`` and ``C`` leaves collinearity unchanged, but those
variables may play different roles elsewhere in the rule. The provider
tries both choices so the rest of the rule can decide which ones work.

Enumerating unused points
-------------------------

1. Collect the distinct variables still unassigned in the predicate.
2. Collect the problem points that the current mapping is not using.
3. For each ordered selection of distinct points, assign them to the
   missing variables and yield the extension. If there are too few
   points, there are no extensions.

For two missing variables and three unused points ``b``, ``c``, and
``d``, the ordered choices are ``(b,c)``, ``(b,d)``, ``(c,b)``,
``(c,d)``, ``(d,b)``, and ``(d,c)``. The provider yields one at a time.
It uses the cache to get the point count without requesting a
geometry index. Internally, it keeps the chosen points at the front
of the available-point list. A partial permutation advances the choices
at the front without visiting every ordering of the unused tail.

The provider collects each missing variable once. For
``cong A M M B`` with ``A`` already assigned, for example, there are
two missing variables, ``M`` and ``B``. An extension supplies one point
for ``M``, which is reused in both argument positions.

Counting and checking assignments
---------------------------------

With :math:`n` unused points and :math:`k` missing variables, the estimate
adds the predicate's base cost to the capped count of ordered selections,
:math:`n(n-1)\cdots(n-k+1)`. In the example, that count is six. The count is zero when
:math:`k > n` and is capped at 100 million before the base cost is added.
The matcher uses the estimate to decide where to search next. The
provider still enumerates the assignments when the estimate reaches
the cap.

When all variables of a predicate have points, the provider builds the
concrete statements and checks each one numerically. For ``coll``, this
is where an assignment with three points off the same line can fail.

The implementation is in ``yuclid/src/matchers/base_provider.cpp``.
