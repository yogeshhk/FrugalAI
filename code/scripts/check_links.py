"""Check that every relative Markdown link in the repo points to a file or folder that exists.

    python code/scripts/check_links.py            # whole repo
    python code/scripts/check_links.py README.md  # one file

External links (http, https, mailto) and pure #anchors are skipped; use check_awesome.py --links for URLs.
Exit code 1 if any relative link is broken.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "sample_wiki"}


def md_files(args):
    if args:
        return [Path(a).resolve() for a in args]
    return [p for p in REPO.rglob("*.md") if not (set(p.relative_to(REPO).parts) & SKIP_DIRS)]


def broken_links(path):
    bad = []
    in_fence = False
    for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        for target in LINK.findall(line):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            file_part = unquote(target.split("#")[0])
            if file_part and not (path.parent / file_part).exists():
                bad.append((n, target))
    return bad


def shown(path):
    """Repo-relative path for display; the full path for a file outside the repo."""
    try:
        return path.relative_to(REPO)
    except ValueError:
        return path


def main(argv=None):
    problems = 0
    files = md_files(argv if argv is not None else sys.argv[1:])
    for path in files:
        for n, target in broken_links(path):
            problems += 1
            print(f"{shown(path)}:{n}: broken link {target}")
    print(f"{len(files)} files checked, {problems} broken relative links")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
