"""Offline tests for _scripts/check_awesome.py. Run: python -m pytest _scripts/tests -q"""

import datetime
from pathlib import Path

import check_awesome as ca

REPO = Path(__file__).resolve().parents[2]   # repo root: _scripts/tests/ sits two levels below it

GOOD = """# Awesome X

<!-- entries:start -->

## Old laptop

- [One](https://example.org/one) - Does a thing on a laptop.
  Hardware: i3, 8 GB. Model: Foo (Apache-2.0). Licence: MIT. Measured: no. Verified: 2026-01-01.

## Phones

No entries yet.

<!-- entries:end -->
"""


def run(text):
    return ca.check_text(text)


class TestFormat:
    def test_good_file_has_no_problems(self):
        entries, problems = run(GOOD)
        assert problems == []
        assert [e["name"] for e in entries] == ["One"]
        assert entries[0]["section"] == "Old laptop"
        assert entries[0]["verified"] == datetime.date(2026, 1, 1)

    def test_missing_markers_is_reported(self):
        _, problems = run("# no markers here\n")
        assert any("markers" in p for p in problems)

    def test_entry_without_description_period_is_bad(self):
        bad = GOOD.replace("on a laptop.", "on a laptop")
        _, problems = run(bad)
        assert any("must look like" in p for p in problems)

    def test_missing_field_is_named(self):
        bad = GOOD.replace(" Measured: no.", "")
        _, problems = run(bad)
        assert any("Measured" in p for p in problems)

    def test_detail_line_must_be_indented_two_spaces(self):
        bad = GOOD.replace("\n  Hardware", "\nHardware")
        _, problems = run(bad)
        assert any("indented" in p for p in problems)

    def test_bad_date_is_reported(self):
        bad = GOOD.replace("2026-01-01", "2026-13-45")
        _, problems = run(bad)
        assert any("real date" in p for p in problems)

    def test_non_ascii_is_reported(self):
        bad = GOOD.replace("Does a thing", "Does a th" + chr(0x00ed) + "ng")
        _, problems = run(bad)
        assert any("non-ASCII" in p for p in problems)

    def test_duplicate_url_is_reported(self):
        dup = GOOD.replace("## Phones", "- [Two](https://example.org/one) - Same link again.\n"
                           "  Hardware: x. Model: y. Licence: MIT. Measured: no. Verified: 2026-01-01.\n\n## Phones")
        _, problems = run(dup)
        assert any("duplicate URL" in p for p in problems)


class TestStaleAndLinks:
    def test_stale_lists_old_entries_only(self):
        entries, _ = run(GOOD)
        assert ca.stale(entries, 365, today=datetime.date(2026, 6, 1)) == []
        assert len(ca.stale(entries, 100, today=datetime.date(2026, 6, 1))) == 1

    def test_relative_link_is_checked_on_disk(self, tmp_path):
        (tmp_path / "there.md").write_text("x", encoding="utf-8")
        entries = [{"name": "ok", "url": "there.md", "section": "s", "verified": None, "line": 1},
                   {"name": "gone", "url": "missing.md", "section": "s", "verified": None, "line": 2}]
        bad = ca.check_links(entries, tmp_path)
        assert [e["name"] for e, _ in bad] == ["gone"]


class TestRealFile:
    def test_awesome_md_passes_its_own_checks(self):
        entries, problems = ca.check_text((REPO / "AWESOME.md").read_text(encoding="utf-8"))
        assert problems == []
        assert len(entries) >= 2

    def test_relative_links_in_awesome_md_exist(self):
        entries, _ = ca.check_text((REPO / "AWESOME.md").read_text(encoding="utf-8"))
        local = [e for e in entries if not e["url"].startswith("http")]
        assert ca.check_links(local, REPO) == []
