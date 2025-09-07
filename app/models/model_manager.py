import os
import requests

# Optional imports for AI functionality
try:
    import torch
except ImportError:
    class TorchStub:
        class cuda:
            @staticmethod
            def is_available():
                return False
            @staticmethod
            def memory_allocated():
                return 0
    torch = TorchStub()

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None
    BitsAndBytesConfig = None

from app.models.prompt_manager import PromptManager


class ModelError(Exception):
    """Custom exception for model-related errors."""
    pass


class ModelManager:
    def __init__(self):
        # Core config
        self.model_name = os.getenv("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        self.quantize = os.getenv("QUANTIZE")
        self.fast_test = os.getenv("FAST_TEST") == "1"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.last_device = self.device

        # External LLM (Akash AI or any HTTP endpoint)
        self.external_llm_url = os.getenv("EXTERNAL_LLM_API_URL")
        self.external_llm_key = os.getenv("EXTERNAL_LLM_API_KEY")
        self.external_llm_hdr = os.getenv("EXTERNAL_LLM_API_KEY_HEADER", "Authorization")
        self.external_llm_scheme = os.getenv("EXTERNAL_LLM_API_KEY_SCHEME", "Bearer")
        # Accepts: "simple" (json {prompt}) or "openai" (OpenAI-compatible Chat Completions)
        self.external_llm_format = os.getenv("EXTERNAL_LLM_FORMAT", "simple").lower()

        # Lazy model holders
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.prompt_manager = PromptManager()

        # Load local model only when not using external URL and not in fast-test mode
        if not self.fast_test and not self.external_llm_url:
            self._load_local_model()

    def _load_local_model(self):
        if not AutoTokenizer or not AutoModelForCausalLM or not pipeline:
            raise ModelError("Transformers library not available. Install transformers or use external API.")
        
        try:
            quantization_config = None
            if self.device == "cuda" and BitsAndBytesConfig:
                if self.quantize == "8bit":
                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                elif self.quantize == "4bit":
                    quantization_config = BitsAndBytesConfig(load_in_4bit=True)

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map='auto' if self.device == 'cuda' else None,
            )
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=512,
                temperature=0.2,
                do_sample=False,
            )
        except Exception as e:
            raise ModelError(f"Failed to load local model: {e}")

    def _external_call(self, prompt):
        if not self.external_llm_url:
            raise ModelError("External LLM URL not configured")

        headers = {}
        if self.external_llm_key:
            if self.external_llm_hdr:
                if self.external_llm_scheme:
                    headers[self.external_llm_hdr] = f"{self.external_llm_scheme} {self.external_llm_key}"
                else:
                    headers[self.external_llm_hdr] = self.external_llm_key

        payload = None
        if self.external_llm_format == "openai":
            model = self.model_name or os.getenv("MODEL_NAME", "gpt-3.5-turbo")
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "stream": False
            }
        else:
            # default "simple" schema
            payload = {"prompt": prompt}

        try:
            response = requests.post(self.external_llm_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            # Try common shapes
            if self.external_llm_format == "openai":
                # OpenAI-compatible: choices[0].message.content or choices[0].text
                try:
                    if isinstance(data.get("choices"), list) and data["choices"]:
                        choice = data["choices"][0]
                        if isinstance(choice, dict):
                            msg = choice.get("message", {})
                            content = msg.get("content") if isinstance(msg, dict) else None
                            if content:
                                return content
                            if choice.get("text"):
                                return choice["text"]
                except Exception:
                    pass
            # Simple: { text: "..." } or { output: "..." }
            return data.get("text") or data.get("output") or str(data)
        except requests.RequestException as e:
            raise ModelError(f"External LLM API call failed: {e}")

    def process(self, text: str, task: str, language: str = "en"):
        if self.fast_test:
            return {"plain_language": f"[{task.upper()} stub] {text[:50]}"}

        prompt = self.prompt_manager.build(task, text, language)

        try:
            if self.external_llm_url:
                result = self._external_call(prompt)
            elif self.generator:
                generated_outputs = self.generator(prompt)
                result = generated_outputs[0]['generated_text'][len(prompt):]
            else:
                raise ModelError("No model or external API available.")
            
            return {"plain_language": result.strip()}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def stream_process(self, text: str, task: str, language: str = "en"):
        if self.fast_test:
            stub_text = f"[{task.upper()} stub] {text[:50]}"
            for word in stub_text.split():
                yield word + " "
            return

        prompt = self.prompt_manager.build(task, text, language)
        
        if self.external_llm_url:
            # Streaming from external URL not implemented in this example
            result = self._external_call(prompt)
            for word in result.split():
                yield word + " "
        elif self.generator:
            # This is a simplified stream, real streaming requires more complex setup
            generated_outputs = self.generator(prompt)
            result = generated_outputs[0]['generated_text'][len(prompt):]
            for word in result.split():
                yield word + " "
        else:
            yield "Error: No model or external API available."

    def analyze_document(self, text: str, mode: str, stream=False, target_lang="en"):
        if stream:
            return self.stream_process(text, mode, target_lang)
        else:
            result = self.process(text, mode, target_lang)
            if result.get("error"):
                raise ModelError(result["message"])
            return result.get("plain_language", "")