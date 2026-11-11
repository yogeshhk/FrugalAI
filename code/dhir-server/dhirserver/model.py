"""Load Dhir 2B with Transformers and generate from chat messages.

The model folder is read, never changed. Dhir ships its architecture as custom code (`modeling_dhir.py`), so loading
needs `trust_remote_code=True`; only load a folder you have read.
"""

import os
import threading
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional

from .toolcalls import strip_control

MODEL_ID = "dhir-2b"


def code_fingerprint(model_dir: str) -> str:
    """SHA-256 over the names and bytes of every .py file in the model folder, in sorted order.

    The folder's own Python (modeling_dhir.py) runs when the server starts, so note this value after reading that code
    and pass it back with --code-sha256 on later runs; a changed file then stops the server before it loads.
    """
    import hashlib
    from pathlib import Path

    root = Path(model_dir)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


@dataclass
class Piece:
    """One streamed fragment, or the final summary (done=True) with counts."""

    text: str = ""
    done: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0


class DhirModel:
    """A loaded Dhir model. `stream_chat` yields text pieces, then one final Piece with the token counts."""

    def __init__(self, model_dir: str, dtype: str = "bf16", threads: Optional[int] = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if threads:
            torch.set_num_threads(threads)
        self.model_dir = model_dir
        self.dtype_name = dtype
        t0 = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        torch_dtype = torch.bfloat16 if dtype == "bf16" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir, dtype=torch_dtype, trust_remote_code=True, low_cpu_mem_usage=True
        )
        if dtype == "int8":
            # Dynamic int8 for the Linear layers: about half the memory of bf16, often faster on a plain CPU.
            self.model = torch.ao.quantization.quantize_dynamic(self.model, {torch.nn.Linear}, dtype=torch.qint8)
        self.model.eval()
        self.load_s = time.perf_counter() - t0
        self._lock = threading.Lock()  # one generation at a time on a small CPU

    def render(self, messages: List[dict], tools: Optional[List[dict]] = None) -> str:
        """The exact prompt text the chat template produces (used by the template check)."""
        return self.tokenizer.apply_chat_template(
            messages, tools=tools or None, add_generation_prompt=True, tokenize=False
        )

    def stream_chat(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        max_tokens: int = 256,
        temperature: float = 0.2,
    ) -> Iterator[Piece]:
        import torch
        from transformers import TextIteratorStreamer

        text = self.render(messages, tools)
        # The template already writes <bos>, so do not add it a second time.
        input_ids = self.tokenizer(text, return_tensors="pt", add_special_tokens=False).input_ids
        prompt_tokens = int(input_ids.shape[-1])
        class CountingStreamer(TextIteratorStreamer):
            """Counts generated token ids exactly (the text pieces are about a word, not a token)."""

            n_tokens = 0

            def put(self, value):
                if not self.next_tokens_are_prompt:
                    self.n_tokens += int(value.numel())
                super().put(value)

        streamer = CountingStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=False, timeout=600)
        gen_kwargs = dict(input_ids=input_ids, max_new_tokens=max_tokens, streamer=streamer)
        if temperature and temperature > 0:
            gen_kwargs.update(do_sample=True, temperature=float(temperature))
        else:
            gen_kwargs.update(do_sample=False)

        errors = []

        def run():
            try:
                with self._lock, torch.inference_mode():
                    self.model.generate(**gen_kwargs)
            except Exception as exc:   # a failed generation must end the stream, or the request would wait for ever
                errors.append(exc)
            finally:
                streamer.end()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        for chunk in streamer:
            clean = strip_control(chunk)
            if clean:
                yield Piece(text=clean)
        thread.join()
        if errors:
            raise errors[0]
        yield Piece(done=True, prompt_tokens=prompt_tokens, completion_tokens=streamer.n_tokens)


def default_model_dir() -> str:
    return os.environ.get("DHIR_MODEL_DIR", "")
