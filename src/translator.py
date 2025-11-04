import json
import re
from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic

from .prompts import LANG_DETECT_SYSTEM, TRANSLATE_SYSTEM, SUPPORTED_DIALECTS


DEVANAGARI = re.compile(r"[\u0900-\u097F]")
GURMUKHI = re.compile(r"[\u0A00-\u0A7F]")
LATIN = re.compile(r"[A-Za-z]")
SPANISH_MARKERS = re.compile(
    r"\b(el|la|los|las|de|que|por|para|con|una?|está|como|qué|cómo)\b", re.I
)
HINGLISH_MARKERS = re.compile(
    r"\b(kya|hai|hain|kaise|kaisa|kyun|kyon|mujhe|tum|aap|mera|hum|ho|nahi|acha)\b", re.I
)
# Punjabi-distinctive Latin transliterations; avoid overlap with Hinglish where possible.
PUNJABI_MARKERS = re.compile(
    r"\b(kive|kiven|kidan|menu|tuhada|tuhanu|asi|asin|tusi|tusin|sanu|changa|changi|pakka|bilkul|haigi|hega|pairi|sat\s?sri\s?akaal|veer|bhenji)\b",
    re.I,
)


@dataclass
class LangGuess:
    dialect: str
    confidence: float
    code_switched: bool


def _heuristic_detect(text: str) -> LangGuess:
    has_dev = bool(DEVANAGARI.search(text))
    has_gur = bool(GURMUKHI.search(text))
    has_latin = bool(LATIN.search(text))
    has_hing = bool(HINGLISH_MARKERS.search(text))
    has_punj = bool(PUNJABI_MARKERS.search(text))
    has_span = bool(SPANISH_MARKERS.search(text))

    if has_gur and has_latin:
        return LangGuess("pa-en", 0.75, True)
    if has_gur:
        return LangGuess("pa", 0.9, False)
    if has_dev and has_latin:
        return LangGuess("hi-en", 0.7, True)
    if has_dev:
        return LangGuess("hi", 0.85, False)
    if has_punj and has_latin:
        return LangGuess("pa-en", 0.7, True)
    if has_hing and has_latin:
        return LangGuess("hi-en", 0.65, True)
    if has_span and has_latin and re.search(r"\b(the|and|with|you|please)\b", text, re.I):
        return LangGuess("es-en", 0.6, True)
    if has_span:
        return LangGuess("es", 0.75, False)
    if has_latin:
        return LangGuess("en", 0.8, False)
    return LangGuess("en", 0.3, False)


def detect_language(text: str, client: Optional[Anthropic] = None, model: str = "claude-haiku-4-5-20251001") -> LangGuess:
    guess = _heuristic_detect(text)
    if guess.confidence >= 0.75 or client is None:
        return guess
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=120,
            system=LANG_DETECT_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        raw = msg.content[0].text.strip()
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        if data.get("dialect") in SUPPORTED_DIALECTS:
            return LangGuess(
                data["dialect"],
                float(data.get("confidence", 0.8)),
                bool(data.get("code_switched", False)),
            )
    except Exception:
        pass
    return guess


class Translator:
    def __init__(self, client: Anthropic, model: str = "claude-haiku-4-5-20251001"):
        self.client = client
        self.model = model

    def translate(self, text: str, source: str, target: str) -> str:
        if source == target:
            return text
        src_name = SUPPORTED_DIALECTS.get(source, source)
        tgt_name = SUPPORTED_DIALECTS.get(target, target)
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            system=TRANSLATE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": f"Source ({src_name}): {text}\n\nTarget ({tgt_name}):",
                }
            ],
        )
        return msg.content[0].text.strip()

    def normalize_for_retrieval(self, text: str, source: str) -> str:
        if source in ("en", "hi-en", "es-en", "pa-en"):
            return text
        return self.translate(text, source=source, target="en")
