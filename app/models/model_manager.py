import os
import json
import math
from typing import Dict, Any, Generator, List

try:
    import torch
except Exception:  # allow running without torch in FAST_TEST
    class _Cuda:
        @staticmethod
        def is_available():
            return False

        @staticmethod
        def memory_allocated():
            return 0

        @staticmethod
        def get_device_name(_):
            return "cpu"

    class _TorchStub:
        cuda = _Cuda()
        float16 = None
        float32 = None

    torch = _TorchStub()
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
except Exception:  # allow running without transformers in FAST_TEST
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None

from app.models.prompt_manager import PromptManager
from app.models.embeddings import Embedder
from app.models.risk_detector import heuristic_risks
from app.utils.logging import logger


class ModelManager:
    def __init__(self, cache=None):
        self.cache = cache
        self.model_name = os.getenv("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        self.quantize = os.getenv("QUANTIZE", "8bit")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.prompt = PromptManager()
        self.embedder = Embedder()
        self.tokenizer = None
        self.model = None
        self.generator = None

    def _load_model(self):
        try:
            if AutoTokenizer is None or AutoModelForCausalLM is None or pipeline is None:
                raise RuntimeError("transformers not available")
            bnb_args = {}
            if self.device == "cuda" and self.quantize in ("8bit", "4bit"):
                try:
                    import bitsandbytes  # noqa: F401
                except Exception:
                    logger.warning("bitsandbytes not available; proceeding without quantization")
                    self.quantize = "none"
                if self.quantize == "8bit":
                    bnb_args = {"load_in_8bit": True, "device_map": "auto"}
                else:
                    bnb_args = {"load_in_4bit": True, "device_map": "auto"}
            else:
                bnb_args = {"device_map": "auto"} if self.device == "cuda" else {}

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                **bnb_args,
            )
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            logger.info("model_loaded", model=self.model_name, device=self.device, quantize=self.quantize)
        except Exception as e:
            logger.exception("model_load_failed", error=str(e))
            self.model = None
            self.tokenizer = None
            self.generator = None

    def gpu_info(self):
        if torch.cuda.is_available():
            mem = torch.cuda.memory_allocated()
            return {"device": torch.cuda.get_device_name(0), "memory": int(mem)}
        return {"device": "cpu", "memory": 0}

    def _chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
        chunks = []
        i = 0
        n = len(text)
        while i < n:
            j = min(n, i + chunk_size)
            chunks.append(text[i:j])
            i = j - overlap
            if i < 0:
                i = 0
        return chunks

    def _summarize_chunks(self, chunks: List[str]) -> str:
        summaries = []
        for ch in chunks:
            prompt = self.prompt.build("summarize", ch)
            out = self._generate_text(prompt, max_new_tokens=180)
            summaries.append(out.strip())
        merged = "\n".join(summaries)
        return merged[:4000]

    def _generate_text(self, prompt: str, max_new_tokens: int = 256) -> str:
        if os.getenv("FAST_TEST") == "1":
            # Lightweight stub for tests/CI
            return (" " + prompt.split("\n")[-1]).strip()[:max_new_tokens]
        if self.generator is None:
            # Lazy load model on first use
            self._load_model()
        if self.generator is None:
            # External fallback
            ext = os.getenv("EXTERNAL_LLM_API_URL")
            if not ext:
                raise RuntimeError("No local model and no EXTERNAL_LLM_API_URL set")
            import requests
            resp = requests.post(ext, json={"prompt": prompt, "max_new_tokens": max_new_tokens}, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("text") or data.get("output") or ""
        res = self.generator(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.3, top_p=0.9)
        return res[0]["generated_text"][len(prompt):]

    def process(self, text: str, task: str = "simplify", language: str = "auto") -> Dict[str, Any]:
        if not text:
            return {"error": "empty_text", "message": "No text provided"}
        cache_key = f"proc:{hash(text)}:{task}:{language}"
        cached = self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        # Chunk + embed + summarize
        chunks = self._chunk_text(text)
        merged_summary = self._summarize_chunks(chunks) if len(text) > 1500 else text

        # Context retrieval
        idxs = self.embedder.search(merged_summary, chunks, top_k=5)
        context = "\n".join([chunks[i] for i, _ in idxs]) if idxs else text

        # Build prompt
        prompt = self.prompt.build("simplify" if task == "simplify" else ("risk" if task == "risk" else "summarize"), context)
        generated = self._generate_text(prompt, max_new_tokens=512)

        # Heuristic risks
        risks = heuristic_risks(text)
        # Optionally refine with LLM
        refine_prompt = (
            "Normalize the following risks into JSON list with fields id,type,clause_excerpt,severity,explanation,suggested_action.\n"
            f"Risks: {json.dumps(risks)}\nJSON:"
        )
        try:
            refined = self._generate_text(refine_prompt, max_new_tokens=256)
            refined_json = self._safe_json_list(refined) or risks
        except Exception:
            refined_json = risks

        # naive clause explanations: first 5 paragraphs summarized
        paras = [p.strip() for p in text.split("\n") if p.strip()][:5]
        clause_expl = []
        for p in paras:
            try:
                pe = self._generate_text(self.prompt.build("summarize", p), max_new_tokens=80).strip()
            except Exception:
                pe = ""
            clause_expl.append({"clause": p[:200], "explanation": pe})

        result = {
            "overview": merged_summary if merged_summary != text else generated[:500],
            "plain_language": generated.strip(),
            "clause_explanations": clause_expl,
            "risks_detected": refined_json,
            "meta": {"model": self.model_name, "device": self.device, "chunks": len(chunks)},
        }
        if self.cache:
            self.cache.set(cache_key, result)
        return result

    def _safe_json_list(self, text: str):
        import re, json
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    def stream_process(self, text: str, task: str = "simplify", language: str = "auto") -> Generator[str, None, None]:
        result = self.process(text, task, language)
        # Simulate token streaming by splitting by space
        tokens = result["plain_language"].split()
        for tok in tokens:
            yield tok + " "
