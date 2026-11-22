"""VoiceForm: the one class every page (Streamlit, Flet) and the command line use. No UI code here.

A page only draws what this class returns and calls its methods when the person acts:

    vf = VoiceForm()                      # engines and folders come from config.yaml
    vf.start("asha_anc_visit", "mr")      # a new, empty record for this form and language
    vf.read("नाव सुनीता पवार ...")          # or vf.hear(wav), vf.hear_file(path), vf.hear_bytes(data)
    vf.rows()                             # each field: value, check, the words it came from
    vf.turn.questions                     # what is still to ask
    vf.read("वय चोवीस")                    # a follow-up or a correction is merged into the same record
    vf.can_save(), vf.confirm_and_save()  # saving is refused until every required field is filled and valid

Engines are loaded when first needed and then kept: the speech model takes about 30 s to load.
"""

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from frugalai_common.machine import lm_models

from . import audio, config, pipeline
from .record import FILLED, MISSING
from .schema import load_forms

LANGS = {"mr": "Marathi", "hi": "Hindi"}   # the languages offered for speech


@dataclass
class ModelInfo:
    """Which language model this language uses, and whether it is ready."""
    model: str
    note: str            # how it runs, in words for the page
    ready: bool          # the server answers, or the .gguf file is there
    fallback: bool       # the preferred model for this language is not ready, so the default is used
    where: str           # the server URL or the .gguf file


@dataclass
class FieldRow:
    """One line of the form table, ready to draw."""
    name: str
    label: str           # in the record's language
    label_en: str
    value: str           # with its unit, or "" when missing
    status: str          # filled, uncertain, invalid, missing
    detail: str          # the words it came from, or why it was not accepted


@dataclass
class Sample:
    """One of the author's own recordings (eval/audio, local only) and the line that was read."""
    id: str
    path: Path
    text: str


class VoiceForm:
    def __init__(self, asr=None, llm=None, forms=None, route: Optional[str] = None,
                 sinks: Optional[List[str]] = None, outbox: Optional[Path] = None, today: Optional[_dt.date] = None):
        """Every argument is optional; by default everything comes from config.yaml. Tests pass fakes."""
        self.forms = forms or load_forms()
        self.route = route or config.ROUTE
        self.sinks = list(sinks or config.SINKS)
        self.outbox = Path(outbox or config.OUTBOX_DIR)
        self.today = today
        self._asr = asr
        self._fixed_llm = llm          # a model given by the caller is used for every language
        self._llms: Dict[str, object] = {}
        self.form = None
        self.lang = None
        self.turn: Optional[pipeline.Turn] = None
        self.source = ""               # where the last utterance came from: microphone, sample <id>, typed
        self.saved: Optional[Dict[str, Path]] = None

    # ------------------------------------------------------------------ setup
    def start(self, form_id: str, lang: str) -> None:
        """A new, empty record for this form and language."""
        if form_id not in self.forms:
            raise KeyError("unknown form %r; choose from %s" % (form_id, list(self.forms)))
        self.form, self.lang = self.forms[form_id], lang
        self.new_record()

    def new_record(self) -> None:
        self.turn, self.source, self.saved = None, "", None

    def model_info(self, lang: Optional[str] = None) -> ModelInfo:
        lang = lang or self.lang
        if self._fixed_llm is not None:
            model = getattr(self._fixed_llm, "model", "given")
            return ModelInfo(model, model, True, False, "")
        if config.LLM_KIND != "http":           # one model, from a .gguf file inside this process (or a fake)
            s = config.llm_settings()
            note = "%s, inside this program" % (Path(s["gguf"]).name if s["gguf"] else s["model"])
            return ModelInfo(s["model"], note, self._llm(s["model"]).available(), False, s["gguf"])
        model = config.FORCED_MODEL or config.model_for_lang(lang, self._server_up)
        preferred = config.FORCED_MODEL or config.PREFERRED_BY_LANG.get(lang, config.DEFAULT_LLM)
        if model == config.DHIR_MODEL:
            note = "Dhir 2B (GGUF) in llama-server"
        elif model == "qwen/qwen3-1.7b":
            note = "Qwen3 1.7B (Q4_K_M) in LM Studio"
        else:
            note = "%s in LM Studio" % model
        return ModelInfo(model, note, self._server_up(model), model != preferred, config.url_for(model))

    def speech_label(self) -> str:
        spec = config.ASR_MODELS.get(config.ASR_NAME, {})
        return spec.get("label", config.ASR_NAME)

    def load_speech(self):
        """Load the speech model now (a page calls this behind a spinner). Returns the backend."""
        if self._asr is None:
            from .asr import get_backend

            self._asr = get_backend(config.ASR_NAME)
        return self._asr

    # ------------------------------------------------------------------ input: each returns the new Turn
    def read(self, text: str, source: str = "typed") -> pipeline.Turn:
        return self._run(text=text, source=source)

    def hear(self, wav, source: str = "microphone") -> pipeline.Turn:
        return self._run(wav=wav, source=source)

    def hear_file(self, path, source: str = "") -> pipeline.Turn:
        return self.hear(audio.load(path), source or Path(path).name)

    def hear_bytes(self, data: bytes, source: str = "microphone") -> pipeline.Turn:
        return self.hear(audio.load_bytes(data), source)

    def _run(self, wav=None, text=None, source="") -> pipeline.Turn:
        if self.form is None:
            raise RuntimeError("call start(form_id, lang) first")
        llm = None if self.route == "rules" else self._llm(self.model_info().model)
        asr = self.load_speech() if wav is not None else None
        previous = self.turn.record if self.turn else None
        self.turn = pipeline.run(self.form, self.lang, wav=wav, text=text, asr=asr, route=self.route, llm=llm,
                                 previous=previous, today=self.today or _dt.date.today())
        self.source, self.saved = source, None
        return self.turn

    # ------------------------------------------------------------------ results
    def rows(self) -> List[FieldRow]:
        """The form table: one row per field, in the form's order."""
        out = []
        fields = self.turn.record.fields if self.turn else {}
        for f in self.form.fields:
            fv = fields.get(f.name)
            status = fv.status if fv else MISSING
            value = "" if fv is None or fv.value is None else str(fv.value)
            if value and f.unit and f.type in ("int", "float"):
                value += " " + f.unit
            detail = "" if fv is None or status == MISSING else (fv.evidence if status == FILLED else (fv.note or fv.evidence))
            out.append(FieldRow(f.name, f.label_in(self.lang), f.label or f.name, value, status, detail))
        return out

    def changed_labels(self) -> List[str]:
        """English labels of the fields the last follow-up added or changed."""
        return [self.form.get(n).label_in("en") or n for n in (self.turn.changed if self.turn else [])]

    def still_needed(self) -> List[str]:
        """Required fields still missing or invalid. Saving is refused while this is not empty."""
        return self.turn.record.missing_required(self.form) if self.turn else [f.name for f in self.form.fields
                                                                                if f.required]

    def can_save(self) -> bool:
        return self.turn is not None and not self.still_needed() and not self.saved

    def confirm_and_save(self) -> Dict[str, Path]:
        """The person has checked the form: save it to every sink in the config. sinks.send refuses an invalid record."""
        from .sinks import send

        if self.turn is None:
            raise RuntimeError("nothing to save yet")
        self.turn.record.confirmed = True
        self.saved = send(self.turn.record, self.form, sinks=self.sinks, outbox=self.outbox)
        return self.saved

    # ------------------------------------------------------------------ sample recordings
    def samples(self) -> List[Sample]:
        """The author's own recordings for this form and language (eval/audio, gitignored, local only)."""
        lines = _script_lines()
        found = []
        for wav in sorted(config.AUDIO_DIR.glob("%s-*_clean.wav" % self.lang)):
            sid = wav.name[: -len("_clean.wav")]
            item = lines.get(sid, {})
            if item.get("form", self.form.id) == self.form.id:
                found.append(Sample(sid, wav, item.get("text", "")))
        return found

    def script_line(self, sample_id: str) -> str:
        """What the speaker read for a sample recording, or "" when it is not one."""
        return _script_lines().get(sample_id, {}).get("text", "")

    # ------------------------------------------------------------------ engines
    def _llm(self, model: str):
        if self._fixed_llm is not None:
            return self._fixed_llm
        if model not in self._llms:
            from .llm import make_llm

            self._llms[model] = make_llm(model)
        return self._llms[model]

    @staticmethod
    def _server_up(model: str) -> bool:
        return lm_models(config.url_for(model)) is not None


_LINES: Optional[dict] = None


def _script_lines() -> dict:
    """Every line of the recording sheet (eval/scripts/<lang>.yaml), by id. Read once."""
    global _LINES
    if _LINES is None:
        _LINES = {}
        for lang in LANGS:
            path = config.SCRIPTS_DIR / ("%s.yaml" % lang)
            if path.exists():
                for item in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
                    _LINES[item["id"]] = item
    return _LINES
