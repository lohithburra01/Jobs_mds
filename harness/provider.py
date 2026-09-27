"""Provider-specific transport. Credentials never enter persisted request bodies."""
import json
import math
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from .store import RunStore, digest


class ProviderError(RuntimeError):
    pass


def load_key(root: Path) -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key and (root / ".env").exists():
        for line in (root / ".env").read_text(encoding="utf-8-sig").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "OPENROUTER_API_KEY":
                key = value.strip().strip("\"'")
    if not key or key in ("your_key_here", "replace_locally_do_not_commit"):
        raise ProviderError("Set OPENROUTER_API_KEY in the environment or the local .env file; never paste it into logs.")
    return key


def http_transport(url: str, body: dict, key: str) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "X-Title": "Local Application Harness"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # No raw upstream error text: it can contain request data or credentials.
        raise ProviderError(f"OpenRouter HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise ProviderError("OpenRouter network timeout or connection failure") from None


def validate_decisions(response: dict, questions: dict) -> dict:
    if not isinstance(response, dict):
        raise ValueError("Jev response must be an object")
    answers = response.get("answers", {})
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ValueError("Jev returned missing or unexpected question IDs")
    for question_id, q in questions.items():
        a = answers[question_id]
        if not isinstance(a, dict):
            raise ValueError("Jev answer must be an object")
        options = set(q["criteria"])
        probs = a.get("probabilities", {})
        if not isinstance(a.get("choice"), str) or a["choice"] not in options or not isinstance(probs, dict) or set(probs) != options:
            raise ValueError("Jev returned invalid choice/probability labels")
        values = list(probs.values())
        confidence = a.get("confidence")
        if any(not isinstance(x, (float, int)) or not math.isfinite(x) or not 0 <= x <= 1 for x in values):
            raise ValueError("Jev returned invalid probabilities")
        if not math.isclose(sum(values), 1.0, abs_tol=.02):
            raise ValueError("Jev probability distribution is incomplete")
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Jev returned invalid confidence")
    return answers


class OpenRouter:
    def __init__(self, store: RunStore, config: dict, key: str, transport=http_transport):
        self.store, self.config, self.key, self.transport = store, config, key, transport

    def _call(self, endpoint: str, body: dict, validation_retry=0) -> dict:
        identity = {"endpoint": endpoint, "body": body}
        if validation_retry:
            identity["validation_retry"] = validation_retry
        request_hash = digest(identity)
        cached = self.store.response(request_hash)
        if cached is not None:
            self._record(request_hash, endpoint, cached)
            return cached
        self.store.request(request_hash, {"endpoint": endpoint, "body": body})
        for attempt in range(3):
            if self.store.state["http_attempts"] >= self.config.get("max_requests", 80):
                raise ProviderError("Run request budget exhausted; saved work can be inspected")
            self.store.state["http_attempts"] += 1
            self.store.event("HTTP_ATTEMPT", request_hash=request_hash, attempt=attempt + 1)
            try:
                result = self.transport(endpoint, body, self.key)
                self.store.write(f"responses/{request_hash}.json", result)
                self._record(request_hash, endpoint, result)
                return result
            except ProviderError as exc:
                message = str(exc).replace(self.key, "[REDACTED]")
                retryable = any(x in message for x in ("429", "500", "502", "503", "524", "529", "network"))
                self.store.event("HTTP_ERROR", request_hash=request_hash, error=message)
                if not retryable or attempt == 2:
                    raise ProviderError(message) from None
                time.sleep(2 ** attempt)
        raise ProviderError("Request failed")

    def _record(self, request_hash, endpoint, response):
        if any(x["request_hash"] == request_hash for x in self.store.state["calls"]):
            return
        # Malformed successful HTTP responses still need accounting before validation.
        metadata = response if isinstance(response, dict) else {}
        usage = metadata.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        cost = usage.get("cost")
        if isinstance(cost, (int, float)):
            self.store.state["cost_usd"] += cost
        self.store.state["calls"].append({"request_hash": request_hash, "endpoint": endpoint,
            "resolved_model": metadata.get("model"), "provider": metadata.get("provider"),
            "id": metadata.get("id"), "usage": usage})
        self.store.save()

    def create(self, instructions: str, payload: dict) -> dict:
        body = {"model": self.config["writer_model"], "temperature": .3,
            "max_tokens": self.config.get("writer_max_tokens", 5000),
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": instructions},
                         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
        if self.config.get("writer_reasoning_effort") is not None:
            body["reasoning"] = {"effort": self.config["writer_reasoning_effort"]}
        result = self._call("https://openrouter.ai/api/v1/chat/completions", body)
        try:
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise ValueError("Writer response is not a JSON object; raw response was saved") from None
        if not isinstance(parsed, dict):
            raise ValueError("Writer returned a non-object JSON value")
        return parsed

    def decide(self, state: dict, questions: dict) -> dict:
        logical_hash = digest({"model": self.config["classifier_model"], "state": state, "questions": questions})
        logical = self.store.state.setdefault("logical_jev_requests", {})
        if logical_hash not in logical:
            logical[logical_hash] = len(questions)
            self.store.state["logical_jev_questions"] = self.store.state.get("logical_jev_questions", 0) + len(questions)
            self.store.save()
        for attempt in range(3):
            result = self._call("https://openrouter.ai/api/alpha/decisions",
                               {"model": self.config["classifier_model"], "state": state, "questions": questions}, validation_retry=attempt)
            try:
                return validate_decisions(result, questions)
            except ValueError:
                self.store.event("INVALID_DECISION_RESPONSE", validation_attempt=attempt)
        raise ValueError("Jev returned invalid answer structures three times; raw responses retained for review")
