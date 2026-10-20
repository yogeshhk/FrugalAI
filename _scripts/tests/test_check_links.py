"""Offline tests for _scripts/check_links.py. Run: python -m pytest _scripts/tests -q"""

import check_links as cl


def write(tmp_path, name, text):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_existing_relative_link_is_fine(tmp_path):
    write(tmp_path, "other.md", "# other\n")
    page = write(tmp_path, "page.md", "See [other](other.md) and [folder](sub/).\n")
    (tmp_path / "sub").mkdir()
    assert cl.broken_links(page) == []


def test_missing_target_is_reported_with_line_number(tmp_path):
    page = write(tmp_path, "page.md", "ok line\nSee [gone](missing.md) here.\n")
    assert cl.broken_links(page) == [(2, "missing.md")]


def test_anchor_is_ignored_but_file_part_is_checked(tmp_path):
    write(tmp_path, "other.md", "# Heading\n")
    page = write(tmp_path, "page.md", "[a](other.md#heading) [b](gone.md#heading) [c](#local)\n")
    assert cl.broken_links(page) == [(1, "gone.md#heading")]


def test_external_links_are_skipped(tmp_path):
    page = write(tmp_path, "page.md", "[x](https://example.org/a) [y](mailto:a@b.c)\n")
    assert cl.broken_links(page) == []


def test_links_inside_code_fences_are_skipped(tmp_path):
    page = write(tmp_path, "page.md", "```\n[not a link](nowhere.md)\n```\nafter\n")
    assert cl.broken_links(page) == []


def test_main_returns_one_on_a_broken_link_and_zero_when_clean(tmp_path, capsys):
    bad = write(tmp_path, "bad.md", "[x](nope.md)\n")
    good = write(tmp_path, "good.md", "no links\n")
    assert cl.main([str(good)]) == 0
    assert cl.main([str(bad)]) == 1
    capsys.readouterr()
