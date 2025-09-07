# app/models/model_manager.py
import os
import re
import json
from typing import Generator, Optional, Union, Dict

_LLAMA_WARNING = (
    "No LLM configured. Using deterministic fallback. "
    "Set OPENAI_API_KEY to enable real model responses."
)

def _looks_hindi(text: str) -> bool:
    # Basic: Devanagari unicode block
    return bool(re.search(r"[\u0900-\u097F]", text))

class ModelError(RuntimeError):
    pass

class ModelManager:
    """
    Thin abstraction over an LLM with graceful dev-mode fallback.

    Modes supported:
      - 'simplify'   : plain-language rewrite (reader-friendly)
      - 'summarize'  : concise bullet points + one-line gist
      - 'translate'  : English ↔ Hindi (min). `target_lang` decides direction.
    """

    def __init__(self):
        self.use_fake = os.getenv("USE_FAKE_MODEL", "").strip() == "1"
        self._client = None
        self._llm_ok = False
        if not self.use_fake:
            try:
                from openai import OpenAI  # type: ignore
                key = os.getenv("OPENAI_API_KEY")
                if key:
                    self._client = OpenAI(api_key=key)
                    self._llm_ok = True
                else:
                    # no key -> fallback
                    self.use_fake = True
            except Exception:
                # openai library not installed or other setup issue
                self.use_fake = True

        # Default model name if using OpenAI
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # -------------------------------
    # Public: analyze_document
    # -------------------------------
    def analyze_document(
        self,
        text: str,
        mode: str,
        stream: bool = False,
        target_lang: Optional[str] = None,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Analyze a document based on mode.

        Args:
            text: input text
            mode: "simplify" | "summarize" | "translate"
            stream: if True, returns generator[str] chunks
            target_lang: for translate mode ('en' or 'hi'). If None, we infer.

        Returns:
            str (sync) OR generator[str] (streaming chunks)
        """
        mode = mode.strip().lower()
        if mode not in {"simplify", "summarize", "translate"}:
            raise ModelError(f"Unsupported mode: {mode}")

        if self.use_fake or not self._llm_ok:
            # Deterministic fallback (dev/test)
            if stream:
                return self._fake_stream(text, mode, target_lang)
            return self._fake_sync(text, mode, target_lang)

        # Real LLM path
        if stream:
            return self._llm_stream(text, mode, target_lang)
        return self._llm_sync(text, mode, target_lang)

    # -------------------------------
    # Fallback (fake) implementation
    # -------------------------------
    def _fake_sync(self, text: str, mode: str, target_lang: Optional[str]) -> str:
        if mode == "simplify":
            # simple sentence shortening (toy)
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            out = []
            for s in sentences:
                s2 = re.sub(r"\b(utilize|leverage|commence|terminate)\b", 
                            lambda m: {"utilize":"use","leverage":"use","commence":"start","terminate":"end"}[m.group(0)], 
                            s, flags=re.I)
                s2 = re.sub(r"\s+", " ", s2).strip()
                if len(s2) > 180:
                    s2 = s2[:177] + "..."
                out.append(s2)
            return " ".join(out)

        if mode == "summarize":
            words = text.strip().split()
            first = " ".join(words[:40]) + ("..." if len(words) > 40 else "")
            bullets = []
            # naive extraction: take first 3 clauses/sentences
            for s in re.split(r'(?<=[.!?])\s+', text.strip())[:3]:
                if s:
                    bullets.append(f"- {s.strip()}")
            gist = (words[:12])
            gist = " ".join(gist) + ("..." if len(words) > 12 else "")
            return f"Summary:\n" + "\n".join(bullets) + f"\n\nGist: {gist}"

        if mode == "translate":
            # Very naive “translation”: tag + passthrough so tests can assert.
            # Direction: infer if not given
            if not target_lang:
                target_lang = "hi" if not _looks_hindi(text) else "en"
            direction = f"en→hi" if target_lang == "hi" else "hi→en"
            return f"[{direction}][FAKE] " + text
        raise ModelError("Unknown mode")

    def _fake_stream(self, text: str, mode: str, target_lang: Optional[str]) -> Generator[str, None, None]:
        # Reuse sync then drip in chunks
        whole = self._fake_sync(text, mode, target_lang)
        chunk_size = 64
        for i in range(0, len(whole), chunk_size):
            yield whole[i : i + chunk_size]

    # -------------------------------
    # Real LLM implementation (OpenAI)
    # -------------------------------
    def _system_prompt(self, mode: str, target_lang: Optional[str]) -> str:
        if mode == "simplify":
            return (
                "You rewrite text into clear, plain, friendly language at ~8th-grade "
                "reading level. Keep meaning, remove jargon, keep key details."
            )
        if mode == "summarize":
            return (
                "You create concise, factual summaries. Output bullet points (3-6) and "
                "finish with one-line 'Gist:'"
            )
        if mode == "translate":
            if not target_lang:
                target_lang = "hi"
            lang_line = "Hindi" if target_lang == "hi" else "English"
            return f"You are a precise translator. Translate faithfully into {lang_line}. Keep names and numbers."
        return "You are helpful."

    def _user_prompt(self, mode: str, text: str, target_lang: Optional[str]) -> str:
        if mode == "simplify":
            return f"Rewrite the following in simple language:\n\n{text}"
        if mode == "summarize":
            return f"Summarize the following. Use bullets and end with 'Gist:' line.\n\n{text}"
        if mode == "translate":
            if not target_lang:
                target_lang = "hi" if not _looks_hindi(text) else "en"
            if target_lang == "hi":
                return f"Translate into Hindi:\n\n{text}"
            return f"Translate into English:\n\n{text}"
        return text

    def _llm_sync(self, text: str, mode: str, target_lang: Optional[str]) -> str:
        try:
            messages = [
                {"role": "system", "content": self._system_prompt(mode, target_lang)},
                {"role": "user", "content": self._user_prompt(mode, text, target_lang)},
            ]
            resp = self._client.chat.completions.create(
                model=self.model_name, messages=messages, stream=False
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            raise ModelError(f"LLM error: {e}")

    def _llm_stream(self, text: str, mode: str, target_lang: Optional[str]) -> Generator[str, None, None]:
        try:
            messages = [
                {"role": "system", "content": self._system_prompt(mode, target_lang)},
                {"role": "user", "content": self._user_prompt(mode, text, target_lang)},
            ]
            stream = self._client.chat.completions.create(
                model=self.model_name, messages=messages, stream=True
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and getattr(delta, "content", None):
                    yield delta.content
        except Exception as e:
            # Surface as ModelError so the route can map it to E502
            raise ModelError(f"LLM stream error: {e}")
