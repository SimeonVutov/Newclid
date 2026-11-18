Setup and usage
===============

Custom rules let you try a geometric theorem without writing a C++ matcher.
This guide builds Yuclid and uses a midpoint rule to show how to inspect
matches, run the solver, and register the same rule from Python.

Install the Newclid workspace
-----------------------------

Use ``uv sync`` if you want to run Newclid from Python. Follow the
:ref:`source installation instructions <building from source>` for
prerequisites, including the Boost setup on Windows. You can then go
straight to :ref:`register-custom-rule-python`.

Compile the Yuclid executable
-----------------------------

The commands in this section build Yuclid directly with CMake for CLI use
and C++ development.

Before building, check that your development environment has the following:

- **CMake 3.28 or newer.** CMake configures the build and locates the Boost
  libraries.
- **A C++23 compiler and standard library with ``std::generator``.**
  Yuclid uses this type to yield candidate mappings one at a time. Check
  that the standard library shipped with your toolchain provides it.
- **Boost 1.83 or newer.** Install the development headers and the
  ``log``, ``log_setup``, ``json``, ``program_options``, and
  ``unit_test_framework`` components. The build uses these for logging,
  JSON output, command-line options, and C++ tests.

Choose the instructions for your platform and run the commands from the
repository root. CMake puts the build files and executable in ``build/``.

Windows
~~~~~~~

The following example uses the Visual Studio generator from PowerShell.
Use the same ``YUCLID_BOOST_DIR`` setting as for workspace installation
if CMake needs help locating Boost.

.. code-block:: powershell

   cmake -S yuclid -B build
   cmake --build build --config Release

For this generator, the Release executable is
``build/src/Release/yuclid.exe``. Adjust the path in the examples below
if you use a different generator.

Linux
~~~~~

.. code-block:: bash

   cmake -S yuclid -B build
   cmake --build build

The executable is ``build/src/yuclid``.

macOS
~~~~~

Use the Linux commands with a compiler and Boost installation that use
the same C++ runtime.

Run the tests
-------------

.. code-block:: bash

   ctest --test-dir build --output-on-failure

With Visual Studio, add ``-C Release`` to select the configuration built above.

Python integration tests
~~~~~~~~~~~~~~~~~~~~~~~~

Install the workspace and its test dependencies with
``uv sync --frozen --group dev``. To run the integration tests against your
local CMake build, put the directory containing the Yuclid executable first
on ``PATH`` before starting pytest. The Python adapter looks up the executable
when it is imported.

**Linux and macOS**

.. code-block:: bash

   PATH="$PWD/build/src:$PATH" .venv/bin/python -m pytest -q yuclid/tests

**Windows (PowerShell, Visual Studio Release build)**

.. code-block:: powershell

   $env:Path = "$PWD\build\src\Release;$env:Path"
   .\.venv\Scripts\python.exe -m pytest -q yuclid/tests

Run a custom rule from the command line
---------------------------------------

On Windows, use ``build/src/Release/yuclid.exe`` in the commands below.

The example identifies a midpoint from collinearity and equal distances.
Both premises are needed: equal distances alone do not make a midpoint.

Save this as ``custom_rules.txt``:

.. code-block:: text

   rule custom_midpoint A B M
   require coll A M B
   require cong A M M B
   conclude midp M A B
   end

Save this as ``problem.txt``. Problem files contain concrete points and
assumptions; rule files contain variables.

.. code-block:: text

   point a 0 0
   point b 2 0
   point m 1 0
   assume coll a m b
   assume cong a m m b
   prove midp m a b

Inspect rule matches
~~~~~~~~~~~~~~~~~~~~

Use ``--mode match`` to list candidate theorem applications before proof
search. Pass the geometry in ``--input-file`` and the rule definitions in
``--input-additional-rules-file``. The ``--use-json`` flag makes the rule
names easy to find in the output.

.. code-block:: bash

   ./build/src/yuclid \
     --mode match \
     --input-file problem.txt \
     --input-additional-rules-file custom_rules.txt \
     --use-json

Look for entries named ``custom_midpoint`` with the conclusion ``midp m a b``.

Prove the goal
~~~~~~~~~~~~~~

Use ``--mode ddar`` to run proof search with the same problem and rule files.

.. code-block:: bash

   ./build/src/yuclid \
     --mode ddar \
     --input-file problem.txt \
     --input-additional-rules-file custom_rules.txt

The proof concludes that ``m`` is the midpoint of ``ab``. Yuclid can also
prove this with a built-in rule. Use the match output above to confirm
that the custom rule produced a candidate.

.. _register-custom-rule-python:

Register a custom rule in Python
--------------------------------

Use ``GeometricSolverBuilder.with_additional_rules`` to pass rules to a
Newclid solver. The example below selects Yuclid as the backend.

Save the following as ``custom_rule_example.py``:

.. code-block:: python

   from newclid.api import GeometricSolverBuilder
   from newclid.jgex.problem_builder import JGEXProblemBuilder
   from newclid.rule import Rule
   from py_yuclid.api_default import HEDefault

   rule = Rule(
       id="custom_midpoint",
       description="Collinearity and equal distances give a midpoint",
       premises_txt=("coll A M B", "cong A M M B"),
       conclusions_txt=("midp M A B",),
   )
   problem = (
       JGEXProblemBuilder(rng=0)
       .with_problem_from_txt(
           "a b = segment a b; m = midpoint m a b ? midp m a b"
       )
       .build()
   )
   solver = (
       GeometricSolverBuilder(api_default=HEDefault())
       .with_additional_rules([rule])
       .build(problem)
   )
   assert solver.run()

Run it in the workspace environment:

.. code-block:: bash

   uv run python custom_rule_example.py

To try it with a Yuclid executable you built directly, put that executable's
directory first on ``PATH``. For example, on Linux:

.. code-block:: bash

   PATH="$PWD/build/src:$PATH" .venv/bin/python custom_rule_example.py

Use a unique rule id. ``with_additional_rules`` skips duplicate ids rather
than replacing an existing rule. See :doc:`architecture` for the round trip.

Supported syntax and limits
---------------------------

Each file can contain several ``rule`` blocks. Each block declares variables,
has at least one ``require`` and one ``conclude``, and ends with ``end``.
Blank lines are allowed; comment lines are not supported.

The C++ custom-rule path accepts these predicate names and argument counts.
For their geometric meanings, see :doc:`../../concepts/predicates`.

.. list-table::
   :header-rows: 1
   :widths: 65 35

   * - Predicates
     - Arguments
   * - ``cong``, ``para``, ``perp``
     - 4 points
   * - ``coll``
     - At least 3 points
   * - ``eqangle``, ``equal_angles``
     - 6 or 8 points
   * - ``cyclic``, ``circle``, ``circumcenter``
     - At least 4 points
   * - ``simtri``, ``simtrir``, ``contri``, ``contrir``,
       ``sameclock``, ``sameside``, ``nsameside``
     - 6 points
   * - ``eqratio``
     - 8 points
   * - ``midp``, ``obtuse_angle``
     - 3 points
   * - ``aconst``, ``rconst``, ``r2const``
     - 4 points and a constant
   * - ``lconst``, ``l2const``
     - 2 points and a constant

Python rule predicates also need a Newclid representation for returned
deductions. Prefer the names in Newclid's predicate reference; C++ aliases
are not necessarily accepted by the Python adapter.

Writing angle constants
~~~~~~~~~~~~~~~~~~~~~~~

If you register a Python rule with Newclid, write the angle in degrees
(``aconst A B C D 90o``) or as a fraction of π
(``aconst A B C D 1pi/2``). When the Yuclid adapter prepares the rule file,
Newclid's angle predicate normalizes the constant to ``1pi/2``. The adapter
then writes ``1/2`` to the file before starting Yuclid. This applies to both
premises and conclusions.

If you write a rule file for the Yuclid executable directly, write the
fraction of π yourself.

.. code-block:: text

   require aconst A B C D 1/2

Here ``1/2`` means π/2 radians, or 90 degrees. Yuclid's rational constant parser
rejects the ``o`` and ``pi`` forms. For lengths and ratios in direct rule
files, use explicit fractions as well, including integers such as ``3/1``.

.. note::

   A rule can have at most **64 distinct variables** and **64 validator
   predicates**, counted across hypotheses and conclusions. The latter is
   not a limit on the total number of predicates; roles are explained in
   :doc:`matching`. Exceeding either limit skips the rule with a warning.

Different variables map to different problem points; repeating a variable
reuses its point. The Python ``allow_point_repetition`` option is not
forwarded to this matcher.

Use letter-prefixed variable names and declare only variables used in the rule.

The matcher logs a warning and skips rules that fail schema validation, for
example when a predicate is unknown or uses an undeclared variable. Unreadable
files and syntax errors, such as a missing ``end`` or a predicate with no
arguments, fail the run. A valid rule
with no matches is not an error. To inspect skipped-rule warnings, run the CLI:
the Python adapter currently captures stderr without forwarding it on successful
runs.

.. important::

   Custom rules are trusted inference rules. Numerical checks reject unsuitable
   point configurations; they do not prove that the rule is a valid theorem.
