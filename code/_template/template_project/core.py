"""The project's one core class, and one job done by plain code so the model is only called for what code cannot do.

Every page (Streamlit app.py, Flet app_flet.py) and the command line call this class and only draw what it returns.
The choices come from config.yaml next to the package, never from constants typed in a page.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_settings(path: Path = ROOT / "config.yaml") -> dict:
    """The config file as a dict; a missing file or key falls back to the defaults."""
    defaults = {"llm": {"kind": "fake", "model": "qwen/qwen3-1.7b", "url": "http://localhost:1234/v1", "gguf": ""}}
    data = (yaml.safe_load(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else None) or {}
    return {**defaults, **data, "llm": {**defaults["llm"], **(data.get("llm") or {})}}


def route(question: str) -> str:
    """"calc" if the question is plain arithmetic, else "lookup". Replace with your own first routing rule."""
    s = question.strip().rstrip("?= ")
    return "calc" if re.fullmatch(r"[\d\s.+\-*/()]+", s) and re.search(r"\d\s*[+\-*/]\s*\d", s) else "lookup"


class Assistant:
    """Rename to what the project does. Engines are built when first needed, from the settings."""

    def __init__(self, settings: dict = None, llm=None):
        self.settings = settings or load_settings()
        self._llm = llm          # tests pass a fake

    def llm(self):
        if self._llm is None:
            from frugalai_common.chat import make_chat   # http server, a GGUF inside this program, or a fake

            self._llm = make_chat(self.settings["llm"])
        return self._llm

    def answer(self, question: str) -> str:
        if route(question) == "calc":
            return str(eval(question.strip().rstrip("?= "), {"__builtins__": {}}))   # digits and operators only
        return self.llm().chat("Answer in one short sentence.", question)
