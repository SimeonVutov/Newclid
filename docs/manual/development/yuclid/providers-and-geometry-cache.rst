Providers and geometry cache
============================

Providers
---------

The matcher coordinates the search for a whole rule. When it works on
one predicate, it calls a *provider* to suggest points or check an
assignment. This gives each predicate a place to use its own geometry
while the matcher handles choices shared by all rules, such as which
predicate to try next and when to backtrack.

For example, suppose a rule asks for two segments of equal length and
the matcher already knows one segment. A general provider can suggest
unused points for the second segment. A specialized provider can use
the known length to look for likely matches first. See :doc:`matching-a-custom-rule`
for where these calls happen in the search.

What the matcher asks a provider
--------------------------------

Each operation in ``PredicateProvider`` receives a planned predicate,
the current mapping, and access to the geometry cache.

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Operation
     - What it does
   * - ``estimate_extensions``
     - Gives the matcher a cost estimate for choosing the next predicate.
   * - ``generate_extensions``
     - Suggests points for the predicate's unassigned variables. It yields
       one extension at a time so the matcher can explore it before
       requesting another.
   * - ``is_satisfied``
     - Checks the predicate numerically once all its variables have points.

The registry selects a provider by predicate name. ``BaseProvider`` is
the fallback for predicates without a specialized implementation. It
tries assignments to unused points and uses the ordinary statement
builders for numerical checks. With a specialized provider, the matcher
can try fewer assignments while using the same search algorithm.

Geometry cache
--------------

Many search branches and rules ask questions about the same points.
The geometry cache keeps reusable information about those points,
such as groups of segments with similar lengths. A provider can look
up a group instead of computing and sorting the same distances each
time it tries an assignment.

``LazyGeometryCache`` is shared by all custom rules in one optimized
matching call for a problem. It builds each index the first time a
provider asks for it. The provider uses the index to find candidates
and applies the rule's current assignments to decide what to suggest.
Candidate generation and numerical validation remain separate steps.

Available providers and indexes
-------------------------------

**Providers**

- :doc:`reference/base-provider` enumerates assignments for predicates without
  a specialized provider.
- :doc:`reference/congruence-provider` uses segment lengths to narrow the
  search for ``cong``.

**Geometry cache**

- :ref:`Point pairs <yuclid-point-pairs>` provide the shared list of endpoints.
- :ref:`Segment-length index <yuclid-segment-length-index>` groups pairs by
  their distance and is used by ``CongProvider``.
- :ref:`Line-orientation index <yuclid-line-orientation-index>` groups pairs
  by the direction of the line through them.

.. toctree::
   :hidden:

   reference/base-provider
   reference/congruence-provider
   reference/geometry-cache-indexes

Adding a provider
-----------------

Start with a predicate that already works through ``BaseProvider``.
A specialized provider changes how the matcher finds assignments while
preserving the accepted cases.

1. Implement the three operations in
   ``yuclid/src/matchers/predicate_provider.hpp``. Use the mapping to
   preserve existing assignments, respect repeated variables, and
   keep points distinct across different variables. Delegate cases
   you have yet to optimize to the fallback.
2. Add an index only when the provider needs reusable geometry. Store
   the index data in ``geometry_cache_types.hpp`` and build it on
   demand in ``lazy_geometry_cache.*``. Let the provider combine
   candidates as needed rather than storing every combination in the cache.
3. Register the provider in
   ``GenericRuleMatcher::add_providers_to_registry`` and add its source
   file to ``yuclid/src/CMakeLists.txt``.
4. Compare against the fallback on small problems. Cover which
   variables already have points, repeated variables, and numerical
   tolerance boundaries. A specialized generator may suggest extra
   assignments, but every assignment that passes the numerical check
   must still be reachable. Compare the assignments or theorem
   contents directly. Equal counts can hide different results.

``yuclid/test/cong_provider.cpp`` and
``yuclid/test/lazy_geometry_cache.cpp`` show how to exercise providers
and indexes. Register new test targets in ``yuclid/test/CMakeLists.txt``.
See :doc:`setup-and-usage` for build and test commands.

To support a new predicate name, first add its argument validation
in ``rules/schema_validator.cpp``, its statement construction in
``statement/statement_builder.cpp``, and its search metadata in
``matchers/predicate_matching_metadata.cpp``. It can use the fallback
provider at first. Rules sent through Newclid also need a Python
predicate representation for returned deductions and constant
preparation where applicable.
