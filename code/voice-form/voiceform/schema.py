"""Form definitions: one YAML file per form in forms/. A new form needs a YAML file, not new code."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from . import config

TYPES = {"text", "int", "float", "date", "enum", "bool", "phone", "bp", "pattern"}


@dataclass
class FieldSpec:
    name: str
    type: str
    required: bool = False
    label: str = ""
    labels: Dict[str, str] = field(default_factory=dict)  # language code -> label
    min: Optional[float] = None
    max: Optional[float] = None
    unit: str = ""
    options: Dict[str, List[str]] = field(default_factory=dict)  # canonical value -> spoken synonyms
    pattern: str = ""
    free_text: bool = False  # a description in the speaker's words; scored by word overlap, not exact match

    def label_in(self, lang: str) -> str:
        return self.labels.get(lang) or self.label or self.name


@dataclass
class FormSpec:
    id: str
    title: str
    fields: List[FieldSpec]
    titles: Dict[str, str] = field(default_factory=dict)
    data_entry_only: bool = False

    def get(self, name: str) -> FieldSpec:
        for f in self.fields:
            if f.name == name:
                return f
        raise KeyError(name)

    @property
    def names(self) -> List[str]:
        return [f.name for f in self.fields]

    def title_in(self, lang: str) -> str:
        return self.titles.get(lang) or self.title


def parse_form(data: dict) -> FormSpec:
    fields = []
    for raw in data.get("fields", []):
        ftype = raw.get("type")
        if ftype not in TYPES:
            raise ValueError(f"form {data.get('id')}: field {raw.get('name')} has unknown type {ftype!r}")
        if ftype == "enum" and not raw.get("options"):
            raise ValueError(f"form {data.get('id')}: enum field {raw.get('name')} needs options")
        if ftype == "pattern" and not raw.get("pattern"):
            raise ValueError(f"form {data.get('id')}: pattern field {raw.get('name')} needs a pattern")
        labels = {k[len("label_"):]: v for k, v in raw.items() if k.startswith("label_")}
        fields.append(FieldSpec(
            name=raw["name"], type=ftype, required=bool(raw.get("required", False)), label=raw.get("label", ""),
            labels=labels, min=raw.get("min"), max=raw.get("max"), unit=raw.get("unit", ""),
            options={k: [str(s) for s in v] for k, v in (raw.get("options") or {}).items()},
            pattern=raw.get("pattern", ""), free_text=bool(raw.get("free_text", False)),
        ))
    names = [f.name for f in fields]
    if len(names) != len(set(names)):
        raise ValueError(f"form {data.get('id')}: duplicate field names")
    titles = {k[len("title_"):]: v for k, v in data.items() if k.startswith("title_")}
    return FormSpec(id=data["id"], title=data.get("title", data["id"]), fields=fields, titles=titles,
                    data_entry_only=bool(data.get("data_entry_only", False)))


def load_form(path: Path) -> FormSpec:
    with open(path, encoding="utf-8") as fh:
        return parse_form(yaml.safe_load(fh))


def load_forms(folder: Path = config.FORMS_DIR) -> Dict[str, FormSpec]:
    forms = {}
    for path in sorted(Path(folder).glob("*.yaml")):
        spec = load_form(path)
        forms[spec.id] = spec
    return forms
