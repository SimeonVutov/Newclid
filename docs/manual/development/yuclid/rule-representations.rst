Rule representations
====================

A custom rule starts as a template. The matcher turns it into a search
plan, assigns its variables to points, and builds concrete theorems from
the assignments that pass. This page follows the representations used at
each step. The :doc:`custom-rule-architecture` page shows where they fit in Yuclid.

Rule schema
-----------

Take the midpoint rule from the architecture page:

.. code-block:: text

   rule midpoint_equal_lengths A B M
   require midp M A B
   conclude cong A M M B
   end

The rule parser stores this as a ``RuleSchema`` with an ID, an ordered list
of variables, and separate lists of hypotheses and conclusions. Each
``RulePredicatePattern`` stores the predicate name and its arguments in
their original order. In ``cong A M M B``, the two occurrences of ``M``
matter because the two segments share that endpoint.

The parser checks the file structure, including duplicate variable
declarations. The matcher then calls ``validate_schema`` to check predicate
names, argument counts, and references to undeclared variables. Geometric
checks need concrete points and happen during matching.

Constants stay in their argument positions. The C++ statement builder uses
``parser/constant_parser.hpp`` to convert them when constructing statements.
If the rule comes through Newclid, ``prepare_rule_arguments`` prepares its
constants for Yuclid without changing point argument positions. See
:doc:`setup-and-usage` for the formats accepted by each entry point.

Rule plan
---------

A ``RulePlan`` prepares the schema for repeated use during search.
Each ``PlannedPredicate`` holds the original pattern, its role and base
cost, and the indices of the variables it needs. The matcher can use
those indices to tell whether a predicate is ready to check.

The declaration ``A B M`` gives ``A = 0``, ``B = 1``, and ``M = 2``.
The two predicates in the example become:

.. list-table::
   :header-rows: 1
   :widths: 36 22 22 20

   * - Pattern
     - Rule side
     - Matching role
     - Variable indices
   * - ``midp M A B``
     - Hypothesis
     - Validator
     - ``[2, 0, 1]``
   * - ``cong A M M B``
     - Conclusion
     - Generator
     - ``[0, 2, 1]``

The indices refer to slots in the rule's variable list. Each slot appears
once in a planned predicate's index list, so the matcher checks the
assignment for ``M`` once when deciding whether ``cong`` is ready. The
original argument list keeps both occurrences for geometric checks and
statement construction.

The plan groups predicates by their search role. The schema still records
which statements serve as hypotheses and which serve as conclusions.
See :doc:`matching-a-custom-rule` for how the roles affect search order.

Partial and complete mappings
-----------------------------

The uppercase letters are placeholders in the rule. The lowercase letters
are actual points in the problem. A *mapping* records which point fills
each placeholder. For instance, ``M → m`` means that whenever the rule
uses ``M``, Yuclid uses the problem point ``m``.

Suppose the matcher has chosen ``a`` for ``A`` and ``m`` for ``M``.
It can keep those choices while looking for a point for ``B``. A suggestion
that fills in one or more missing variables is called an *extension*.
Here the extension proposes ``b`` for ``B``.

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Search step
     - ``A``
     - ``B``
     - ``M``
   * - Before the extension
     - ``a``
     - Unassigned
     - ``m``
   * - Suggested extension
     - Keep ``a``
     - Try ``b``
     - Keep ``m``
   * - After applying it
     - ``a``
     - ``b``
     - ``m``

With all three choices in place, Yuclid can check whether ``m`` is the
midpoint of ``ab`` and whether the two segments have equal length. To try
a different point for ``B``, the matcher can undo that choice and keep
``A → a`` and ``M → m``.

In the code, ``MappingState`` stores the current choices by index, and a
provider supplies new choices as a ``MappingExtension``. A snapshot lets
the matcher restore its earlier choices. Once every variable has a point,
the matcher converts the state to a ``RuleMapping`` so the statement
builder can look up points by variable name.

Statements and theorems
-----------------------

A ``Statement`` represents a concrete geometric relation. Given the
mapping above, ``build_statements_from_pattern`` turns
``cong A M M B`` into the equality ``|a-m| = |m-b|``. Its result is a list
because some patterns produce multiple statements. For example,
``coll A B C D`` expands into consecutive collinear triples.

``build_theorem_from_rule_schema`` builds statements for both sides and
combines them into an ordinary Yuclid ``Theorem`` with the original rule
ID. The theorem contains the concrete hypotheses and conclusions of one
candidate application.
