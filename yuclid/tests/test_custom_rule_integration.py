import json
import logging
import subprocess

import numpy as np
import pytest
from newclid.agent.follow_deductions import FollowDeductions
from newclid.all_rules import DEFAULT_RULES
from newclid.api import GeometricSolverBuilder, PythonDefault
from newclid.jgex.problem_builder import JGEXProblemBuilder
from newclid.problem import PredicateConstruction
from newclid.rule import Rule
from py_yuclid.api_default import HEDefault
from py_yuclid.yuclid_adapter import (
    YUCLID_PATH,
    YuclidAdapter,
    _predicate_to_yuclid,
    _write_custom_rule_setup,
)


@pytest.mark.parametrize(
    ("predicate", "expected"),
    [
        ("aconst D C B A 1pi/2", "aconst D C B A 1/2"),
        ("aconst A B A C 90o", "aconst A B A C 1/2"),
        ("aconst A B C D 270o", "aconst A B C D 1/2"),
        ("aconst A B C D -90o", "aconst A B C D 1/2"),
        ("aconst A B C D 0pi/2", "aconst A B C D 0/1"),
        ("rconst D C B A 6/4", "rconst D C B A 3/2"),
        ("r2const D C B A 6/4", "r2const D C B A 3/2"),
        ("lconst B A 3", "lconst B A 3/1"),
        ("l2const B A 9", "l2const B A 9/1"),
        ("coll C B A A", "coll C B A A"),
        ("cong A B A C", "cong A B A C"),
    ],
)
def test_custom_rule_serialization_preserves_variable_positions(predicate, expected):
    rule = Rule(
        id="constant_serialization",
        description="Constant serialization",
        premises_txt=(predicate,),
        conclusions_txt=(predicate,),
    )
    original_rule = rule.model_dump()

    assert _write_custom_rule_setup(rule) == [
        f"rule {rule.id} {' '.join(sorted(rule.variables))}",
        f"require {expected}",
        f"conclude {expected}",
        "end",
    ]
    assert rule.model_dump() == original_rule


@pytest.mark.parametrize(
    ("predicate", "expected"),
    [
        ("aconst b a d c 270o", "aconst a b c d 1/2"),
        ("rconst d c b a 2/3", "rconst a b c d 3/2"),
        ("r2const d c b a 2/3", "r2const a b c d 3/2"),
        ("lconst b a 3", "lconst a b 3/1"),
        ("l2const b a 9", "l2const a b 9/1"),
    ],
)
def test_goal_constant_serialization_keeps_existing_canonicalization(
    predicate, expected
):
    construction = PredicateConstruction.from_str(predicate)
    assert _predicate_to_yuclid(construction) == expected


class TestYuclidCustomRuleIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.rng = np.random.default_rng(42)
        logging.getLogger("newclid.agent").setLevel(logging.WARNING)
        self.problem_builder = JGEXProblemBuilder(rng=self.rng)
        self.he_adapter = YuclidAdapter()
        self.follow_deductions = FollowDeductions(self.he_adapter)
        self.solver_builder = GeometricSolverBuilder(
            rng=self.rng, api_default=HEDefault(self.he_adapter)
        ).with_deductive_agent(self.follow_deductions)

    def test_builder_configures_custom_rules_and_clears_previous_rules(
        self, monkeypatch
    ):
        custom_rule = Rule(
            id="custom_collinearity",
            description="Reorder collinear points",
            premises_txt=("coll A B C",),
            conclusions_txt=("coll C B A",),
        )
        problem_setup = self.problem_builder.with_problem_from_txt(
            "a b = segment a b; m = midpoint m a b ? cong a m b m"
        ).build()

        def unexpected_run():
            pytest.fail("Building the solver must not invoke Yuclid")

        monkeypatch.setattr(self.he_adapter, "_run_yuclid", unexpected_run)
        self.solver_builder.with_additional_rules([custom_rule]).build(problem_setup)
        assert self.he_adapter.custom_rules == [custom_rule]
        assert self.he_adapter.goals == list(problem_setup.goals)
        assert self.he_adapter.problem_name == problem_setup.name

        self.solver_builder.with_rules(list(DEFAULT_RULES)).build(problem_setup)
        assert self.he_adapter.custom_rules == []
        assert self.he_adapter.goals == list(problem_setup.goals)

    def test_python_backend_accepts_selected_rules(self):
        problem_setup = self.problem_builder.with_problem_from_txt(
            "a b = segment a b; m = midpoint m a b ? cong a m b m"
        ).build()
        builder = GeometricSolverBuilder(
            rng=self.rng, api_default=PythonDefault(use_sympy_ar=False)
        )

        solver = builder.build(problem_setup)
        assert solver.rules == builder.rules

    @pytest.mark.parametrize("file_kind", ["missing", "directory"])
    def test_unreadable_custom_rule_file_is_an_error(self, tmp_path, file_kind):
        rules_file = tmp_path / "rules.txt"
        if file_kind == "directory":
            rules_file.mkdir()

        result = subprocess.run(
            [
                str(YUCLID_PATH),
                "--mode",
                "match",
                "--use-json",
                "--input-additional-rules-file",
                str(rules_file),
            ],
            input="point a 0 0\npoint b 1 0\n",
            text=True,
            capture_output=True,
        )
        assert result.returncode == 1
        assert "custom rules file" in result.stderr
        assert str(rules_file) in result.stderr
        assert not result.stdout

    @pytest.mark.parametrize("angle", ["1pi/2", "90o", "270o", "-90o"])
    def test_custom_angle_rule_reaches_yuclid(self, tmp_path, angle):
        rule = Rule(
            id="custom_right_angle",
            description="A right angle gives perpendicular lines",
            premises_txt=(f"aconst A B C D {angle}",),
            conclusions_txt=("perp A B C D",),
        )
        self.he_adapter.custom_rules = [rule]
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text(self.he_adapter.precomputation_custom_rules_str)

        result = subprocess.run(
            [
                str(YUCLID_PATH),
                "--mode",
                "match",
                "--use-json",
                "--log-level",
                "warning",
                "--input-additional-rules-file",
                str(rules_file),
            ],
            input="point a 0 0\npoint b 1 0\npoint c 0 2\npoint d 0 3\n",
            text=True,
            capture_output=True,
            check=True,
        )
        theorems = json.loads(result.stdout)
        custom_theorems = [
            theorem for theorem in theorems if theorem["name"] == rule.id
        ]

        # Match mode checks our rule directly, even if built-in rules could prove the goal.
        assert len(custom_theorems) == 8
        assert any(
            theorem["hypotheses"]
            == [{"name": "aconst", "points": ["a", "b", "c", "d", "1/2"]}]
            and theorem["conclusions"]
            == [{"name": "perp", "points": ["a", "b", "c", "d"]}]
            for theorem in custom_theorems
        )

    def test_valid_custom_rule_runs_after_invalid_rule_is_skipped(self, caplog):
        """
        Uses a problem (IMO 2012 P5) that the standard engine CANNOT solve natively.
        By injecting a custom cheat rule that bridges the assumptions to the goal,
        we guarantee the engine must use our rule to succeed.
        """

        custom_rule = Rule(
            id="custom_imo_cheat",
            description="Cheat rule: intersecting lines imply congruent segments",
            premises_txt=("coll X Y Z", "coll X W U"),
            conclusions_txt=("cong X U X Z",),
        )

        invalid_rule = Rule(
            id="invalid_collinearity",
            description="Collinearity requires at least three points",
            premises_txt=("coll X Y",),
            conclusions_txt=("coll X Y Z",),
        )
        self.solver_builder.with_additional_rules([invalid_rule, custom_rule])

        # 'a' as midpoint of 'b' and 'c' guarantees that AB = AC and they form a line.
        # This makes our custom rule numerically true!
        problem_txt = (
            "c a b = r_triangle c a b; d = foot d c a b; x = on_line x c d;"
            " k = on_line k a x, on_circle k b c; l = on_line l b x, on_circle l a c;"
            " m = on_line m a l, on_line m b k"
            " ? cong m k m l"
        )

        problem_setup = self.problem_builder.with_problem_from_txt(problem_txt).build()

        self.he_adapter.problem_name = "custom_rule_integration"
        solver = self.solver_builder.build(problem_setup)

        success = solver.run()

        # Ensure the engine reached the goal
        assert success, "The solver failed to reach the goal."

        assert any(
            record.name == "py_yuclid.yuclid_adapter"
            and record.levelno == logging.WARNING
            and "invalid_collinearity" in record.message
            and "expects at least 3 arguments" in record.message
            for record in caplog.records
        )

        # Verify it was the custom rule that was mapped back
        custom_rule_obj = next(
            r for r in self.solver_builder.rules if r.id == "custom_imo_cheat"
        )

        matches = self.he_adapter.rule_matches(custom_rule_obj, problem_setup)

        assert len(matches) > 0, "No matches were found for the custom rule."
        assert matches[0].rule.id == "custom_imo_cheat"

        deductions_used = self.he_adapter.ordered_deductions_for_problem(problem_setup)
        rule_ids_used = [deduction.rule.id for deduction in deductions_used]
        assert "custom_imo_cheat" in rule_ids_used, (
            "Rule hasn't been used in the proof."
        )
