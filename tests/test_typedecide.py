from types import SimpleNamespace

import pytest

import typedecide as td
from typedecide.backends.jev import JevBackend
from typedecide.backends.laya import LayaBackend
from typedecide.backends.semif import SemIfBackend
from typedecide.backends.thisthat import ThisThatBackend


def questions():
    return (
        td.choice("route", "Which route?", {"billing": "Billing", "account": "Account"}),
        td.noul("eligible", "Eligible?", true="Policy permits it", false="Policy does not permit it"),
        td.score("severity", "How severe?", ["low", "high"]),
    )


def test_canonical_question_builders_and_answer_validation():
    route, eligible, severity = questions()
    assert route.option_ids == ("billing", "account")
    assert eligible.option_ids == ("false", "true")
    assert severity.option_ids == ("0", "1")
    with pytest.raises(ValueError, match="false, true"):
        td.Question("bad", "noul", "Question", (td.Option("true", "yes"), td.Option("false", "no")))


def test_package_owned_100_case_benchmark_has_valid_shape():
    cases = td.validate_real_world_suite()
    assert len(cases) == 100
    assert len({case.family for case in cases}) == 10
    assert all(case.gold in case.question.option_ids for case in cases)


def test_benchmark_cli_exposes_unified_backend_choices():
    from typedecide.cli import parser

    run = next(action for action in parser()._subparsers._group_actions if action.dest == "command")
    choices = run.choices["run"]._option_string_actions["--backend"].choices
    assert set(choices) == {"thisthat", "jev", "semif", "laya"}


def test_jev_backend_normalizes_all_primitives():
    route, eligible, severity = questions()
    response = SimpleNamespace(
        model="jev-1.13.0",
        usage=SimpleNamespace(input_tokens=19, output_tokens=4),
        answers={
            "route": SimpleNamespace(probabilities={"billing": 0.8, "account": 0.2}, confidence=0.6),
            "eligible": SimpleNamespace(noul=0.7),
            "severity": SimpleNamespace(probabilities={0: 0.25, 1: 0.75}, confidence=0.5),
        },
    )
    client = SimpleNamespace(system_one=lambda **kwargs: response, close=lambda: None)
    result = JevBackend(client, "jev-1.13.0").predict({"text": "state"}, (route, eligible, severity))
    assert result.answers["route"].selected == "billing"
    assert result.answers["eligible"].probabilities == pytest.approx((0.3, 0.7))
    assert result.answers["severity"].score == pytest.approx(0.75)
    assert result.input_tokens == 19


def test_jev_score_uses_ordered_level_probabilities():
    question = td.score("severity", "How severe?", ["low", "medium", "high"])
    response = SimpleNamespace(
        model="jev-1.13.0",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        answers={"severity": SimpleNamespace(probabilities={0: 0.0, 1: 0.57, 2: 0.43}, confidence=0.35)},
    )
    result = JevBackend(SimpleNamespace(system_one=lambda **kwargs: response, close=lambda: None), "jev-1.13.0").predict(
        "state", (question,)
    )
    answer = result.answers["severity"]
    assert answer.selected == "1"
    assert answer.probabilities == pytest.approx((0.0, 0.57, 0.43))
    assert answer.score == pytest.approx(1.43)


def test_laya_backend_normalizes_rounded_maps_and_noul():
    route, eligible, severity = questions()
    agent = SimpleNamespace(predict=lambda state, native: {
        "model": "laya-rl-agent",
        "answers": {
            "route": {"probabilities": {"billing": 0.3333, "account": 0.6666}, "confidence": 0.4},
            "eligible": {"noul": 0.8, "confidence": 0.6},
            "severity": {"probabilities": {"0": 0.2, "1": 0.8}, "confidence": 0.6},
        },
        "usage": {"input_tokens": 8, "output_tokens": 0},
    })
    result = LayaBackend(agent, "convaiinnovations/laya", "typed-decisions").predict(
        {"text": "state"}, (route, eligible, severity)
    )
    assert sum(result.answers["route"].probabilities) == pytest.approx(1.0)
    assert result.answers["route"].selected == "account"
    assert result.answers["eligible"].selected == "true"
    assert result.answers["severity"].score == pytest.approx(0.8)


def test_laya_score_uses_ordered_level_probabilities():
    question = td.score("severity", "How severe?", ["low", "medium", "high"])
    agent = SimpleNamespace(predict=lambda state, native: {
        "answers": {"severity": {"probabilities": {"0": 0.0, "1": 0.57, "2": 0.43}}},
    })
    result = LayaBackend(agent, "model", "typed-decisions").predict("state", (question,))
    answer = result.answers["severity"]
    assert answer.selected == "1"
    assert answer.probabilities == pytest.approx((0.0, 0.57, 0.43))
    assert answer.score == pytest.approx(1.43)


def test_semif_backend_maps_canonical_rows(monkeypatch):
    route, eligible, severity = questions()
    responses = iter([
        {"probabilities": [0.8, 0.2], "total_seconds": 0.01, "input_tokens": 3},
        {"probabilities": [0.4, 0.6], "total_seconds": 0.02, "input_tokens": 4},
        {"probabilities": [0.1, 0.9], "total_seconds": 0.03, "input_tokens": 5},
    ])
    monkeypatch.setattr("semif_phase1.direct.score", lambda *args: next(responses))
    backend = SemIfBackend("model", "tokenizer", {"source": "model", "revision": "a" * 40})
    result = backend.predict({"text": "state"}, (route, eligible, severity))
    assert result.answers["route"].selected == "billing"
    assert result.answers["eligible"].selected == "true"
    assert result.answers["severity"].score == pytest.approx(0.9)
    assert result.input_tokens == 12


def test_semif_score_uses_ordered_option_probabilities(monkeypatch):
    question = td.score("severity", "How severe?", ["low", "medium", "high"])
    monkeypatch.setattr(
        "semif_phase1.direct.score",
        lambda *args: {"probabilities": [0.0, 0.57, 0.43], "total_seconds": 0.01, "input_tokens": 1},
    )
    backend = SemIfBackend("model", "tokenizer", {"source": "model", "revision": "a" * 40})
    answer = backend.predict("state", (question,)).answers["severity"]
    assert answer.selected == "1"
    assert answer.probabilities == pytest.approx((0.0, 0.57, 0.43))
    assert answer.score == pytest.approx(1.43)


def test_thisthat_score_uses_ordered_option_probabilities():
    question = td.score("severity", "How severe?", ["low", "medium", "high"])
    decider = SimpleNamespace(decide=lambda state, questions: [SimpleNamespace(probabilities=[0.0, 0.57, 0.43], index=1)])
    answer = ThisThatBackend(decider, "model").predict("state", (question,)).answers["severity"]
    assert answer.selected == "1"
    assert answer.probabilities == pytest.approx((0.0, 0.57, 0.43))
    assert answer.score == pytest.approx(1.43)