"""Check AWESOME.md: entry format, required fields, duplicates, ASCII-only text.

Usage (from the repo root):
    python _scripts/check_awesome.py                  # format checks only, offline
    python _scripts/check_awesome.py --links          # also check that every URL resolves
    python _scripts/check_awesome.py --stale-days 365 # list entries whose Verified date is older

Exit status 1 if there is a format problem or a broken link. Staleness only warns.
The script checks shape, not merit: whether an entry meets the criteria is the maintainer's call.
"""
import argparse
import datetime
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

START = "<!-- entries:start -->"
END = "<!-- entries:end -->"
FIELDS = ("Hardware", "Model", "Licence", "Measured", "Verified")
ENTRY = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)\) - (?P<desc>[A-Z].*\.)$")
DATE = re.compile(r"Verified: (\d{4}-\d{2}-\d{2})")
PLACEHOLDER = "No entries yet."


def check_text(text):
    """Return (entries, problems). Each entry is a dict with name, url, section, verified (date or None)."""
    problems, entries = [], []
    lines = text.splitlines()

    for n, line in enumerate(lines, 1):
        if any(ord(ch) > 127 for ch in line):
            problems.append("line %d: non-ASCII character (use plain ASCII text)" % n)

    if START not in lines or END not in lines:
        problems.append("missing %s or %s markers" % (START, END))
        return entries, problems

    first, last = lines.index(START), lines.index(END)
    section = ""
    i = first + 1
    while i < last:
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
        elif line.startswith("- ["):
            m = ENTRY.match(line)
            if not m:
                problems.append("line %d: entry must look like '- [Name](URL) - Description.'" % (i + 1))
            else:
                detail = lines[i + 1] if i + 1 < len(lines) else ""
                if not detail.startswith("  ") or detail.startswith("   "):
                    problems.append("line %d: the line after the entry must be indented by exactly two spaces" % (i + 2))
                missing = [f for f in FIELDS if (f + ": ") not in detail]
                if missing:
                    problems.append("line %d: entry '%s' is missing field(s): %s" % (i + 2, m.group("name"), ", ".join(missing)))
                d = DATE.search(detail)
                verified = None
                if d:
                    try:
                        verified = datetime.date.fromisoformat(d.group(1))
                    except ValueError:
                        problems.append("line %d: Verified date is not a real date" % (i + 2))
                elif "Verified: " in detail:
                    problems.append("line %d: Verified must be YYYY-MM-DD" % (i + 2))
                entries.append({"name": m.group("name"), "url": m.group("url"), "section": section,
                                "verified": verified, "line": i + 1})
                i += 1  # skip the detail line
        elif line.strip() and not line.startswith("  ") and line != PLACEHOLDER:
            pass  # prose under a heading is allowed
        i += 1

    seen_url, seen_name = {}, {}
    for e in entries:
        for table, key, label in ((seen_url, e["url"].lower(), "URL"), (seen_name, e["name"].lower(), "name")):
            if key in table:
                problems.append("line %d: duplicate %s '%s' (first on line %d)" % (e["line"], label, key, table[key]))
            else:
                table[key] = e["line"]
    return entries, problems


def stale(entries, days, today=None):
    today = today or datetime.date.today()
    return [e for e in entries if e["verified"] is not None and (today - e["verified"]).days > days]


def check_links(entries, base_dir, timeout=10):
    """Return a list of (entry, reason) for URLs that do not resolve. Relative links are checked on disk."""
    bad = []
    for e in entries:
        url = e["url"]
        if url.startswith("http"):
            ok = False
            for method in ("HEAD", "GET"):
                try:
                    req = urllib.request.Request(url, method=method, headers={"User-Agent": "frugalai-awesome-check"})
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        ok = resp.status < 400
                    break
                except urllib.error.HTTPError as exc:
                    if method == "HEAD" and exc.code in (403, 405):
                        continue
                    bad.append((e, "HTTP %d" % exc.code))
                    ok = True  # reported already
                    break
                except Exception as exc:  # network trouble: report, do not crash
                    bad.append((e, type(exc).__name__))
                    ok = True
                    break
            if not ok:
                bad.append((e, "no response"))
        elif not (Path(base_dir) / url.split("#")[0]).exists():
            bad.append((e, "path not found"))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check AWESOME.md")
    ap.add_argument("--file", default=str(Path(__file__).resolve().parents[1] / "AWESOME.md"))   # repo root
    ap.add_argument("--links", action="store_true", help="also check that every URL resolves")
    ap.add_argument("--stale-days", type=int, default=None, help="list entries verified longer ago than this")
    args = ap.parse_args(argv)

    path = Path(args.file)
    entries, problems = check_text(path.read_text(encoding="utf-8"))
    for p in problems:
        print("PROBLEM:", p)

    broken = []
    if args.links:
        broken = check_links(entries, path.parent)
        for e, why in broken:
            print("BROKEN LINK: %s (%s): %s" % (e["name"], e["url"], why))

    if args.stale_days is not None:
        for e in stale(entries, args.stale_days):
            print("STALE: %s, verified %s" % (e["name"], e["verified"]))

    print("%d entries, %d problems, %d broken links" % (len(entries), len(problems), len(broken)))
    return 1 if (problems or broken) else 0


if __name__ == "__main__":
    sys.exit(main())
