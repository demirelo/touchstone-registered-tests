"""A provider whose decisions come from a model backend through a prompt-hash cache (spec 5.4)."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm_actor import CapExceeded, PromptCache, build_payload, build_state, canonical_request, parse_action, request_hash
from .base import Action, ProviderView
from .honest import HonestMax


@dataclass
class ActorCounters:
    calls: int = 0
    cache_hits: int = 0
    fallbacks: int = 0
    rounds: int = 0
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


class LLMProvider:
    """Provider role only: effort plus an offer or abstain, never an exit. A malformed response falls back to
    honest-max for that round and is counted. A cap raised by the backend propagates."""
    name = "llm_provider"

    def __init__(self, backend, cache: PromptCache, rendered_rule: str, params, feedback: list, T: int, counters: ActorCounters) -> None:
        self.backend, self.cache, self.rendered_rule, self.params, self.feedback, self.T, self.counters = backend, cache, rendered_rule, params, list(feedback), int(T), counters

    def act(self, view: ProviderView) -> Action:
        self.counters.rounds += 1
        payload = build_payload(self.backend, "action", self.rendered_rule, state=build_state(view, self.feedback, self.T))
        key = request_hash(self.backend.name, self.backend.model, "action", payload)
        resp = self.cache.get(key)
        if resp is None:
            try:
                resp = self.backend.complete("action", payload)
            except CapExceeded as e:
                if e.response is not None:                 # an overrun on this request: its paid response is cached so a restart never pays for it again
                    self.cache.put(key, canonical_request(self.backend.name, self.backend.model, "action", payload), e.response)
                raise                                      # a pre-dispatch refusal carries no response and creates no cache entry
            self.cache.put(key, canonical_request(self.backend.name, self.backend.model, "action", payload), resp)
            self.counters.calls += 1
            for k in ("input_tokens", "output_tokens"):
                self.counters.usage[k] += int(resp.get("usage", {}).get(k) or 0)
        else:
            self.counters.cache_hits += 1
        action = parse_action(resp.get("data"), self.params)
        if action is None:
            self.counters.fallbacks += 1
            return HonestMax().act(view)
        return action
