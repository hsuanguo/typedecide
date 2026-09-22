import http.client
import json
import threading
import time
from types import SimpleNamespace

import pytest

import typedecide as td
from typedecide.backends.jev import JevBackend
from typedecide.backends.laya import LayaBackend
from typedecide.backends.semif import SemIfBackend
from typedecide.backends.thisthat import ThisThatBackend
from typedecide.server import App, backend_config, bind, model_name_for, playground_html
from typedecide.wire import (
    WireError,
    decision_confidence,
    encode_system_one,
    parse_system_one,
)


def scripted_answers(questions):
    answers = {}
    for question in questions:
        count = len(question.option_ids)
        if question.type == "noul":
            probabilities = (0.25, 0.75)
        elif question.type == "score":
            probabilities = [0.0] * count
            probabilities[0] = 0.2
            probabilities[-1] = 0.8
            probabilities = tuple(probabilities)
        else:
            probabilities = [0.0] * count
            probabilities[0] = 0.8
            probabilities[1] = 0.2
            probabilities = tuple(probabilities)
        selected = max(range(count), key=probabilities.__getitem__)
        answers[question.id] = td.Answer(
            question.id,
            question.option_ids,
            probabilities,
            question.option_ids[selected],
            max(probabilities),
            score=(
                sum(
                    index * probability
                    for index, probability in enumerate(probabilities)
                )
                if question.type == "score"
                else None
            ),
        )
    return answers


class ScriptedBackend:
    name = "scripted"

    def __init__(self):
        self.states = []
        self.closed = False

    def predict(self, state, questions):
        self.states.append(state)
        return td.Response(
            self.name,
            "requested-model",
            "resolved-model",
            scripted_answers(questions),
            3.0,
            None,
            None,
        )

    def close(self):
        self.closed = True


def sample_payload():
    return {
        "model": "jev-latest",
        "state": {"ticket": "My card was charged twice."},
        "questions": {
            "route": {
                "type": "choice",
                "instructions": "Which route?",
                "criteria": {"billing": "Billing", "account": None},
            },
            "urgent": {"type": "noul", "instructions": "Is this urgent?"},
            "severity": {
                "type": "score",
                "instructions": "How severe?",
                "criteria": ["low", "high"],
            },
        },
    }


def test_decision_confidence_tracks_peak_concentration():
    assert decision_confidence((1.0, 0.0)) == pytest.approx(1.0)
    assert decision_confidence((0.5, 0.5)) == pytest.approx(0.0)
    assert decision_confidence((0.9, 0.06, 0.04)) == pytest.approx(0.85)


def test_parse_preserves_order_and_official_defaults():
    state, questions = parse_system_one(sample_payload())
    route, urgent, severity = questions
    assert state == {"ticket": "My card was charged twice."}
    assert route.option_ids == ("billing", "account")
    assert route.criteria[1].description == ""
    assert urgent.option_ids == ("false", "true")
    assert urgent.criteria[0].description == "no"
    assert urgent.criteria[1].description == "yes"
    assert severity.option_ids == ("0", "1")


def test_structured_instructions_become_compact_json():
    _, questions = parse_system_one(
        {
            "state": "resume",
            "questions": {
                "same": {
                    "type": "noul",
                    "instructions": {
                        "question": "Same person as `candidate`?",
                        "candidate": {"name": "Ada"},
                    },
                    "criteria": {"true": ["matched"], "false": "different"},
                }
            },
        }
    )
    question = questions[0]
    assert question.instructions == (
        '{"question":"Same person as `candidate`?","candidate":{"name":"Ada"}}'
    )
    assert question.criteria[1].description == '["matched"]'


def test_encode_official_answer_shapes():
    state, questions = parse_system_one(sample_payload())
    encoded = encode_system_one(ScriptedBackend().predict(state, questions), questions)
    assert encoded["model"] == "resolved-model"
    assert encoded["usage"] == {"input_tokens": None, "output_tokens": None}
    assert list(encoded["answers"]) == ["route", "urgent", "severity"]
    route = encoded["answers"]["route"]
    assert route == {
        "type": "choice",
        "choice": "billing",
        "probabilities": {"billing": 0.8, "account": 0.2},
        "confidence": pytest.approx(0.6),
    }
    assert "confidence" not in encoded["answers"]["urgent"]
    assert encoded["answers"]["urgent"]["noul"] == pytest.approx(0.75)
    severity = encoded["answers"]["severity"]
    assert severity["score"] == pytest.approx(0.8)
    assert severity["legend"] == {"0": "low", "1": "high"}
    assert list(severity["probabilities"]) == ["0", "1"]


def test_validation_errors_name_the_field():
    with pytest.raises(WireError, match="at most 10") as error:
        parse_system_one(
            {
                "state": "x",
                "questions": {
                    "severity": {
                        "type": "score",
                        "instructions": "How severe?",
                        "criteria": [str(index) for index in range(11)],
                    }
                },
            }
        )
    assert error.value.field == "questions.severity.criteria"
    with pytest.raises(WireError, match="non-empty object") as missing:
        parse_system_one({"state": "x", "questions": {}})
    assert missing.value.field == "questions"


def test_backend_config_forwards_device_selectively():
    assert backend_config("jev", "jev-1.13.0", "cuda") == {"model": "jev-1.13.0"}
    assert backend_config("laya", None, "auto") == {}
    assert backend_config("laya", None, "cuda") == {"device": "cuda"}
    assert backend_config("semif", None, "cpu") == {"device": "cpu"}
    assert backend_config("thisthat", "org/model", "cpu") == {
        "model": "org/model",
        "device": "cpu",
    }


def test_model_name_uses_backend_default():
    backend = SimpleNamespace()
    assert model_name_for(JevBackend(backend, "ignored"), None) == "jev-1.13.0"
    assert (
        model_name_for(LayaBackend(backend, "ignored", "typed-decisions"), None)
        == "convaiinnovations/laya"
    )
    assert (
        model_name_for(ThisThatBackend(backend, "ignored"), None)
        == "flock-io/this-that-model-1.0"
    )
    assert (
        model_name_for(SemIfBackend(backend, backend, {}), "Qwen/custom")
        == "Qwen/custom"
    )


def test_evaluate_serializes_predict_calls():
    class SlowBackend(ScriptedBackend):
        def __init__(self):
            super().__init__()
            self.inside = 0
            self.max_inside = 0
            self.guard = threading.Lock()

        def predict(self, state, questions):
            with self.guard:
                self.inside += 1
                self.max_inside = max(self.max_inside, self.inside)
            time.sleep(0.05)
            with self.guard:
                self.inside -= 1
            return super().predict(state, questions)

    backend = SlowBackend()
    app = App(backend, "local-model", None)
    threads = [
        threading.Thread(target=app.evaluate, args=(sample_payload(),))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert backend.max_inside == 1


def test_playground_is_served_with_the_api():
    page = playground_html()
    assert "Let the model decide" in page
    assert "/v1/systemone" in page
    assert "Let the model run" in page
    assert 'id="key-jump"' in page
    backend = ScriptedBackend()
    with running(App(backend, "convaiinnovations/laya", None)) as server:
        status, body = request(server, "GET", "/")
        assert status == 200
        assert "typedecide" in body
        status, payload = request_json(server, "GET", "/v1/models")
        assert status == 200
        assert payload["models"] == [
            {
                "name": "convaiinnovations/laya",
                "description": "scripted served by typedecide",
                "release_date": "local",
            }
        ]
        status, payload = request_json(
            server, "POST", "/v1/systemone", sample_payload()
        )
        assert status == 200
        assert payload["model"] == "resolved-model"
        assert payload["answers"]["urgent"]["noul"] == pytest.approx(0.75)
        assert backend.states == [{"ticket": "My card was charged twice."}]
        status, payload = request_json(
            server,
            "POST",
            "/v1/systemone",
            {"state": "x", "questions": {}},
        )
        assert status == 422
        assert payload["error"]["field"] == "questions"
    backend.close()
    assert backend.closed


def test_api_key_gates_v1_routes_only():
    app = App(ScriptedBackend(), "local-model", "secret")
    with running(app) as server:
        status, _ = request(server, "GET", "/")
        assert status == 200
        status, payload = request_json(
            server, "POST", "/v1/systemone", sample_payload()
        )
        assert status == 401
        assert payload["error"]["message"] == "Missing or invalid API key."
        status, _ = request_json(
            server,
            "GET",
            "/v1/models",
            headers={"Authorization": "Bearer no"},
        )
        assert status == 401
        status, payload = request_json(
            server,
            "POST",
            "/v1/systemone",
            sample_payload(),
            headers={"Authorization": "Bearer secret"},
        )
        assert status == 200
        assert payload["model"] == "resolved-model"


class running:
    def __init__(self, app):
        self.app = app
        self.server = None
        self.thread = None

    def __enter__(self):
        self.server = bind(self.app, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.server

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        return False


def request(server, method, path, body=None, headers=None):
    host, port = server.server_address[:2]
    connection = http.client.HTTPConnection(host, port, timeout=5)
    raw = None if body is None else json.dumps(body).encode()
    merged = dict(headers or {})
    if raw is not None:
        merged["Content-Type"] = "application/json"
    connection.request(method, path, body=raw, headers=merged)
    response = connection.getresponse()
    text = response.read().decode()
    status = response.status
    connection.close()
    return status, text


def request_json(server, method, path, body=None, headers=None):
    status, text = request(server, method, path, body, headers)
    return status, json.loads(text)
