import os
import json
import hashlib
from typing import Dict, Any, Generator, List
from concurrent.futures import ThreadPoolExecutor

# Torch stub for tests
try:
    import torch
except Exception:
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

# Transformers stub for tests
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
except Exception:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None

# App imports
from app.models.prompt_manager import PromptManager
from app.models.embeddings import Embedder
from app.models.risk_detector import detect_risks, full_clause_analysis
from app.utils.logging import logger

import time
import requests


class ModelError(Exception):
    """Custom exception for model-related errors."""
    pass


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
        self._executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)

    def _translate(self, text: str, target_lang: str = "hi") -> str:
        """Very simple bilingual translation dictionary (stub)."""
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

    def _load_model(self):
        try:
            if AutoTokenizer is None or AutoModelForCausalLM is None or pipeline is None:
                raise RuntimeError("transformers not available")
            
            bnb_args = {}
            if self.device == "cuda" and self.quantize in ("8bit", "4bit"):
                try:
                    import bitsandbytes
                except ImportError:
                    logger.warning("bitsandbytes not available; proceeding without quantization")
                    self.quantize = "none"
                
                if self.quantize == "8bit":
                    bnb_args = {"load_in_8bit": True, "device_map": "auto"}
                else:
                    bnb_args = {"load_in_4bit": True, "device_map": "auto"}
            elif self.device == "cuda":
                bnb_args = {"device_map": "auto"}

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

    def _unload_model(self):
        """Unloads the model to free up memory."""
        if self.model:
            try:
                del self.model
                del self.tokenizer
                del self.generator
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                logger.info("model_unloaded")
            except Exception as e:
                logger.error("failed_to_unload_model", error=str(e))

    def gpu_info(self):
        if torch.cuda.is_available():
            mem = torch.cuda.memory_allocated()
            return {"device": torch.cuda.get_device_name(0), "memory": int(mem)}
        return {"device": "cpu", "memory": 0}

    def _chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
        chunks = []
        n = len(text)
        i = 0
        while i < n:
            end = min(i + chunk_size, n)
            chunks.append(text[i:end])
            if end == n:
                break
            i = end - overlap
            if i < 0:
                i = 0
        return chunks

    def _summarize_chunk(self, chunk: str) -> str:
        prompt = self.prompt.build("summarize", chunk)
        return self._generate_text(prompt, max_new_tokens=180).strip()

    def _summarize_chunks(self, chunks: List[str]) -> str:
        if not chunks:
            return ""
        
        summaries = self._executor.map(self._summarize_chunk, chunks)
        merged = "\n".join(summaries)
        return merged[:4000]

    def _generate_text(self, prompt: str, max_new_tokens: int = 256) -> str:
        if os.getenv("FAST_TEST") == "1":
            return (" " + prompt.split("\n")[-1]).strip()[:max_new_tokens]
        
        if self.generator is None:
            self._load_model()

        if self.generator is None:
            ext = os.getenv("EXTERNAL_LLM_API_URL")
            if not ext:
                raise RuntimeError("No local model and no EXTERNAL_LLM_API_URL set")
            try:
                resp = requests.post(ext, json={"prompt": prompt, "max_new_tokens": max_new_tokens}, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                return data.get("text") or data.get("output") or ""
            except requests.exceptions.RequestException as e:
                raise ModelError(f"External LLM API call failed: {e}")

        try:
            res = self.generator(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.3, top_p=0.9)
            return res[0]["generated_text"][len(prompt):]
        except Exception as e:
            raise ModelError(f"Local model generation failed: {e}")

    def process(self, text: str, task: str = "simplify", language: str = "auto") -> Dict[str, Any]:
        if not text:
            return {"error": "empty_text", "message": "No text provided"}
        
        cache_key = hashlib.sha256(f"{text}:{task}:{language}".encode('utf-8')).hexdigest()
        cached = self.cache.get(cache_key) if self.cache else None
        if cached:
            return cached

        chunks = self._chunk_text(text)
        merged_summary = self._summarize_chunks(chunks) if len(text) > 1500 else text

        idxs = self.embedder.search(merged_summary, chunks, top_k=5)
        context = "\n".join([chunks[i] for i, _ in idxs]) if idxs else text

        prompt = self.prompt.build(task, context)
        try:
            generated = self._generate_text(prompt, max_new_tokens=512)
        except ModelError as e:
            return {"error": "model_generation_failed", "message": str(e)}

        # The fix: Correctly call full_clause_analysis for the 'risk' task.
        if task == "risk":
            risks = full_clause_analysis(text)
        else:
            risks = detect_risks(text)

        refine_prompt = (
            "Normalize the following risks into JSON list with fields id,type,clause_excerpt,severity,explanation,suggested_action.\n"
            f"Risks: {json.dumps(risks)}\nJSON:"
        )
        try:
            refined = self._generate_text(refine_prompt, max_new_tokens=256)
            refined_json = self._safe_json_list(refined) or risks
        except Exception:
            refined_json = risks

        paras = [p.strip() for p in text.split("\n") if p.strip()][:5]
        clause_expl = []
        for p in paras:
            try:
                pe = self._generate_text(self.prompt.build("summarize", p), max_new_tokens=80).strip()
                clause_expl.append({"clause": p[:200], "explanation": pe})
            except Exception:
                clause_expl.append({"clause": p[:200], "explanation": "Could not generate explanation."})
        
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
        # Use a non-greedy regex to match only the first JSON list.
        m = re.search(r"\[.*?\]", text, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON list from LLM output.")
            return None

    def stream_process(self, text: str, task: str = "simplify", language: str = "auto") -> Generator[str, None, None]:
        result = self.process(text, task, language)
        if "error" in result:
            yield json.dumps(result)
            return

        tokens = result["plain_language"].split()
        for tok in tokens:
            yield tok + " "

    def analyze_document(self, text: str, mode: str, stream=False, target_lang="hi"):
        if stream:
            return self.stream_process(text, task=mode, language=target_lang)
        else:
            result = self.process(text, task=mode, language=target_lang)
            if "error" in result:
                raise ModelError(result["message"])
            return result["plain_language"]