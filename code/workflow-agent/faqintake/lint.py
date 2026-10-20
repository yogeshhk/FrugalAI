"""The FAQ house format as code. Every rule comes from faqs/README.md and CONCEPT_INTAKE.md; the real entries are
the test: all of them must pass (see tests). Findings are (level, message); only 'error' fails an entry."""

import re
from typing import List, Tuple

Finding = Tuple[str, str]
EM, EN = chr(0x2014), chr(0x2013)                 # written as code points so this file holds no dash character
DASHES = (EM, EN, " -- ", "---")


def lint(raw: str, draft: bool = False) -> List[Finding]:
    """draft=True checks a machine draft: it must close with '*Unverified draft ...*' (a draft may never claim
    '*Verified*', because no source has been checked) and its Sources may say 'to verify'."""
    f: List[Finding] = []
    if draft:
        if re.search(r"^\*Verified\s", raw, re.M):
            f.append(("error", "a draft must not claim '*Verified*': use '*Unverified draft <date> ...*'"))
        if not re.search(r"^\*Unverified draft\s", raw, re.M):
            f.append(("error", "missing '*Unverified draft <date> ...*' closing line"))
    if not re.search(r"^# FAQ:\s*\S", raw, re.M):
        f.append(("error", "missing title line '# FAQ: <question>'"))
    for label, name in (("Question", "Question"), ("Answer", "Answer"), ("The fallacy", "fallacy paragraph")):
        if not re.search(r"^\*\*" + label, raw, re.M):
            f.append(("error", f"missing '**{label}...**' paragraph ({name})"))
    if "## Sources" not in raw:
        f.append(("error", "missing '## Sources' section"))
    else:
        src = raw.split("## Sources", 1)[1]
        if not re.search(r"\]\(https?://", src) and "to verify" not in src.lower():
            f.append(("error", "Sources has no link and no 'to verify' note"))
    if not draft and not re.search(r"^\*Verified\s", raw, re.M):
        f.append(("error", "missing '*Verified <date> ...*' closing line"))
    for d in DASHES:
        if d in raw:
            f.append(("error", f"dash not allowed: {d.strip() or 'double hyphen'!r} (use a colon, comma or parentheses)"))
            break
    answer = re.search(r"\*\*Answer[^*]*\*\*\s*(.*?)(?=\n\*\*[A-Z]|\n## |\Z)", raw, re.S)
    if answer and len(answer.group(1).split()) < 40:
        f.append(("error", "Answer is too short (under 40 words)"))
    fallacy = re.search(r"\*\*The fallacy[^*]*\*\*\s*(.*?)(?=\n## |\n\*Verified|\Z)", raw, re.S)
    if fallacy and len(fallacy.group(1).split()) < 15:
        f.append(("error", "fallacy paragraph is too short (under 15 words)"))
    if re.search(r"\bthis chapter\b", raw, re.I):
        f.append(("warning", "avoid 'this chapter' (no cross-references to the book)"))
    return f


def errors(raw: str, draft: bool = False) -> List[str]:
    return [m for lvl, m in lint(raw, draft=draft) if lvl == "error"]
