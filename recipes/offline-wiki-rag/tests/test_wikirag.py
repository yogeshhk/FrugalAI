"""Offline tests: no model, no server. Run from the repo root: pytest recipes/offline-wiki-rag/tests -v"""

import json
import time
from pathlib import Path

import pytest

from wikirag.answer import build_prompt, strip_think
from wikirag.bm25 import BM25
from wikirag.index import WikiIndex
from wikirag.router import route, safe_eval
from wikirag.textutil import chunk_markdown, tokenize

RECIPE = Path(__file__).resolve().parents[1]
SAMPLE = RECIPE / "sample_wiki"


class TestChunking:
    def test_splits_by_heading_and_keeps_heading(self):
        text = "# Top\n\nintro\n\n## A\n\nalpha text\n\n## B\n\nbeta text\n"
        chunks = chunk_markdown(text, "n.md")
        assert [(c.heading, c.text) for c in chunks] == [("Top", "intro"), ("A", "alpha text"), ("B", "beta text")]

    def test_long_paragraph_is_split_under_the_limit(self):
        chunks = chunk_markdown("# H\n\n" + ("word " * 400), "n.md", max_chars=200)
        assert len(chunks) > 1
        assert all(len(c.text) <= 200 for c in chunks)

    def test_empty_sections_are_dropped(self):
        assert chunk_markdown("# A\n\n# B\n\ntext", "n.md")[0].heading == "B"


class TestTokenizer:
    def test_lowercase_and_stopwords(self):
        assert tokenize("What is the Water FILTER?") == ["water", "filter"]

    def test_devanagari_words_stay_whole(self):
        word = "".join(chr(c) for c in (0x0924, 0x0941, 0x0933, 0x0938, 0x0940))   # Marathi word with vowel signs
        assert tokenize("%s water" % word) == [word, "water"]


class TestBM25:
    def test_matching_document_ranks_first(self):
        docs = [tokenize(t) for t in ("mango sapling watering", "dal tadka ghee", "train ticket seat")]
        scores = BM25(docs).scores(tokenize("mango watering"))
        assert scores.index(max(scores)) == 0

    def test_unknown_terms_score_zero(self):
        assert BM25([["a"], ["b"]]).scores(["zzz"]) == [0.0, 0.0]

    def test_empty_corpus(self):
        assert BM25([]).scores(["a"]) == []


class TestIndexSync:
    def _wiki(self, tmp_path):
        (tmp_path / "a.md").write_text("# A\n\napples are red", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n\nbananas are yellow", encoding="utf-8")
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "x.md").write_text("# X\n\nsecret", encoding="utf-8")
        return tmp_path

    def test_first_sync_adds_and_skips_hidden_folders(self, tmp_path):
        idx = WikiIndex()
        stats = idx.sync(self._wiki(tmp_path))
        assert sorted(stats["added"]) == ["a.md", "b.md"]
        assert idx.search("secret") == []

    def test_second_sync_changes_nothing(self, tmp_path):
        wiki = self._wiki(tmp_path)
        idx = WikiIndex()
        idx.sync(wiki)
        stats = idx.sync(wiki)
        assert stats["added"] == stats["updated"] == stats["removed"] == []
        assert stats["unchanged"] == 2

    def test_edit_and_delete_are_picked_up(self, tmp_path):
        wiki = self._wiki(tmp_path)
        idx = WikiIndex()
        idx.sync(wiki)
        time.sleep(0.01)
        (wiki / "a.md").write_text("# A\n\napples are green and sour now", encoding="utf-8")
        (wiki / "b.md").unlink()
        stats = idx.sync(wiki)
        assert stats["updated"] == ["a.md"] and stats["removed"] == ["b.md"]
        assert idx.search("bananas") == []
        assert idx.search("sour")[0].chunk.source == "a.md"

    def test_save_and_load_round_trip(self, tmp_path):
        (tmp_path / "wiki").mkdir()
        wiki = self._wiki(tmp_path / "wiki")
        idx = WikiIndex()
        idx.sync(wiki)
        path = tmp_path / "idx" / "index.json"
        idx.save(path)
        loaded = WikiIndex.load(path)
        assert loaded.search("apples")[0].chunk.source == "a.md"
        assert loaded.sync(wiki)["unchanged"] == 2

    def test_load_of_missing_file_gives_empty_index(self, tmp_path):
        assert WikiIndex.load(tmp_path / "nope.json").chunks == []


class TestDenseFusion:
    def test_embedder_can_rescue_a_query_with_no_word_overlap(self, tmp_path):
        (tmp_path / "a.md").write_text("# A\n\nfeline sleeps on the sofa", encoding="utf-8")
        (tmp_path / "b.md").write_text("# B\n\nthe train leaves at seven", encoding="utf-8")

        def fake_embed(texts):   # toy 2-d embedding: dimension 0 = cat-ish, 1 = train-ish
            return [[1.0, 0.0] if ("feline" in t or "kitten" in t) else [0.0, 1.0] for t in texts]

        idx = WikiIndex()
        idx.sync(tmp_path, embedder=fake_embed)
        assert idx.has_vectors()
        assert idx.search("kitten", k=1) == []                                   # BM25 alone: no overlap
        assert idx.search("kitten", k=1, embedder=fake_embed)[0].chunk.source == "a.md"


class TestRouter:
    def test_arithmetic_goes_to_calculator(self):
        r = route("What is 12 * (3 + 4)?")
        assert (r.kind, r.payload) == ("calc", "12 * (3 + 4)")
        assert safe_eval(r.payload) == 84

    def test_plain_question_goes_to_retrieval(self):
        assert route("When is the electricity bill due?").kind == "retrieve"

    def test_a_bare_number_is_not_a_calculation(self):
        assert route("2024").kind == "retrieve"

    @pytest.mark.parametrize("bad", ["__import__('os')", "1 +", "2 ** 100000", "abs(3)"])
    def test_safe_eval_rejects_anything_else(self, bad):
        with pytest.raises((ValueError, SyntaxError)):
            safe_eval(bad)


class TestPrompt:
    def test_think_blocks_are_removed(self):
        assert strip_think("<think>hmm</think>  The answer is 6.") == "The answer is 6."

    def test_context_is_capped(self):
        idx = WikiIndex()
        idx.sync(SAMPLE)
        hits = idx.search("water", k=5)
        prompt = build_prompt("q?", hits, max_context_chars=300)
        assert prompt.count("[") <= 3          # only a few source tags fit

    def test_no_think_flag_appends_switch(self):
        assert build_prompt("q?", [], no_think=True).endswith("/no_think")
        assert "no_think" not in build_prompt("q?", [])


class TestSampleWikiRetrieval:
    """A real bar: the shipped evaluation questions must be found in the top 3."""

    def test_every_question_hits_at_3(self):
        idx = WikiIndex()
        idx.sync(SAMPLE)
        questions = json.loads((RECIPE / "eval" / "questions.json").read_text(encoding="utf-8"))
        misses = [q["q"] for q in questions
                  if q["source"] not in [h.chunk.source for h in idx.search(q["q"], k=3)]]
        assert misses == []
