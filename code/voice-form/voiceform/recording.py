"""Getting the author's recordings in: a printable recording sheet, and an importer for phone recordings.

1. python -m voiceform sheet           writes eval/RECORDING.md (what to say, file names to use)
2. record on a phone or laptop, one file per line, named <id>_clean.<ext> or <id>_noisy.<ext>
3. python -m voiceform import <folder>  converts every file to 16 kHz mono WAV in eval/audio/
"""

import re
from pathlib import Path
from typing import List

from . import audio, config
from .evaluate import load_scripts

AUDIO_EXT = {".wav", ".m4a", ".mp3", ".ogg", ".opus", ".webm", ".aac", ".flac", ".3gp", ".amr"}
NAME_RE = re.compile(r"^((?:mr|hi)-[a-z]+-\d{2})_(clean|noisy)$")


def write_sheet(langs=("mr", "hi")) -> Path:
    lines = ["# Recording sheet", "",
             "Synthetic lines: every name and number is made up. Speak naturally, at field pace; small slips are fine",
             "(say the line again only if you lose your place). One file per line.", "",
             "- **clean**: every line, in a quiet room. File name: `<id>_clean` plus any audio extension.",
             "- **noisy**: only the `heldout` lines, with a fan, TV or street noise in the background. "
             "File name: `<id>_noisy`.",
             "- Then: `python -m voiceform import <folder with your files>`", ""]
    for lang in langs:
        items = load_scripts(lang)
        lines += [f"## {config.LANG_NAMES[lang]} ({len(items)} lines; noisy: "
                  f"{sum(1 for i in items if i['set'] == 'heldout')})", ""]
        for it in items:
            if it.get("text"):
                noisy = " + noisy" if it["set"] == "heldout" else ""
                lines += [f"**{it['id']}** ({it['form']}, {it['set']}{noisy})", "", it["text"], ""]
            else:
                lines += [f"**{it['id']}** ({it['form']}, free speech, clean only). Say these facts in your own "
                          "words, in any order:", "", it["facts"], ""]
    path = config.EVAL_DIR / "RECORDING.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def import_folder(folder) -> List[Path]:
    """Convert recordings named <id>_clean.* or <id>_noisy.* into eval/audio/<id>_<condition>.wav."""
    known = {it["id"] for lang in ("mr", "hi") for it in load_scripts(lang)}
    done, skipped = [], []
    for p in sorted(Path(folder).iterdir()):
        if p.suffix.lower() not in AUDIO_EXT:
            continue
        m = NAME_RE.match(p.stem.lower())
        if not m or m.group(1) not in known:
            skipped.append(p.name)
            continue
        out = config.AUDIO_DIR / f"{m.group(1)}_{m.group(2)}.wav"
        audio.save_wav(out, audio.load(p))
        done.append(out)
    for name in skipped:
        print(f"[skip] {name}: name must be <id>_clean or <id>_noisy with an id from the scripts")
    return done
