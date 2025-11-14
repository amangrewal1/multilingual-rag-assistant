import json
import re
from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic

from .prompts import SAFETY_SYSTEM


INJECTION_PATTERNS = [
    r"ignore (all |the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (your|the) (system|instructions)",
    r"you are now",
    r"reveal (your|the) (system prompt|instructions)",
    r"print (your|the) system prompt",
    r"developer mode",
    r"jailbreak",
]

HARD_REFUSE_PATTERNS = [
    r"\b(make|build|synthesize)\b.*\b(bomb|explosive|bioweapon|nerve agent)\b",
    r"\bkill myself\b",
    r"\bhow to (hack|phish) \w+ account",
]


@dataclass
class SafetyVerdict:
    verdict: str          # allow | refuse | clarify
    category: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.verdict == "allow"


def _regex_triage(text: str) -> Optional[SafetyVerdict]:
    lowered = text.lower()
    for pat in HARD_REFUSE_PATTERNS:
        if re.search(pat, lowered):
            return SafetyVerdict("refuse", "harmful", "matches hard-block pattern")
    for pat in INJECTION_PATTERNS:
        if re.search(pat, lowered):
            return SafetyVerdict("refuse", "prompt_injection", "instruction-override attempt")
    if len(text.strip()) < 3:
        return SafetyVerdict("clarify", "ambiguous", "too short to interpret")
    return None


class SafetyGate:
    def __init__(self, client: Anthropic, model: str = "claude-haiku-4-5-20251001"):
        self.client = client
        self.model = model

    def check(self, text: str) -> SafetyVerdict:
        early = _regex_triage(text)
        if early is not None:
            return early
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=160,
                system=SAFETY_SYSTEM,
                messages=[{"role": "user", "content": text}],
            )
            raw = msg.content[0].text.strip()
            data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
            return SafetyVerdict(
                verdict=data.get("verdict", "allow"),
                category=data.get("category", "ok"),
                reason=data.get("reason", ""),
            )
        except Exception as e:
            return SafetyVerdict("allow", "ok", f"gate-fallback: {e}")
