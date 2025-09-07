import time

class ModelManager:
    """
    Handles text processing tasks:
    - simplify
    - summarize
    - translate (English <-> Hindi)
    """

    def __init__(self):
        pass

    def _simplify(self, text: str) -> str:
        # Naive simplification: shorten long words, reduce jargon
        return " ".join([w if len(w) < 10 else w[:7] + "…" for w in text.split()])

    def _summarize(self, text: str) -> str:
        # Naive summarization: return first 2 sentences
        sentences = text.split(".")
        return ".".join(sentences[:2]).strip() + "."

    def _translate(self, text: str, target_lang: str = "hi") -> str:
        # Mock bilingual translation dictionary
        dictionary = {
            "hello": "नमस्ते",
            "world": "दुनिया",
            "good": "अच्छा",
            "bad": "खराब"
        }
        if target_lang == "hi":
            return " ".join([dictionary.get(w.lower(), w) for w in text.split()])
        elif target_lang == "en":
            reverse_dict = {v: k for k, v in dictionary.items()}
            return " ".join([reverse_dict.get(w, w) for w in text.split()])
        else:
            return text

    def analyze_document(self, text: str, mode: str, stream=False, target_lang="hi"):
        """
        Main document analysis entrypoint.
        Supports streaming if stream=True.
        """
        if mode == "simplify":
            output = self._simplify(text)
        elif mode == "summarize":
            output = self._summarize(text)
        elif mode == "translate":
            output = self._translate(text, target_lang)
        else:
            raise ValueError("Unsupported mode")

        if stream:
            for word in output.split():
                yield word + " "
                time.sleep(0.05)
        else:
            return output
