"""Run the answer evaluation with another chat model, into its own results folder (the main results/ stay untouched).

    python eval/run_other_model.py MODEL URL OUT_FOLDER SYSTEMS SETS [LIMIT]
    python eval/run_other_model.py dhir-2b http://localhost:1236/v1 results_dhir agent dev,heldout

Run from code/quantum-wiki with the frugalai_common path set (see README). Chat goes to URL (for Dhir 2B, ZenteiQ's llama-server,
see ../dhir-server/README.md). Embeddings come from the on-disk cache (parsed/embeddings.json) and are not fetched from URL:
a text that is not cached stops the run with a message. The agent system uses the model for about a third of the questions;
the struct and naive systems call it for every question (about 19 s each with Dhir 2B on the author's laptop).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) < 6:
    sys.exit(__doc__)
model, url, out_name, systems, sets = sys.argv[1:6]
limit = int(sys.argv[6]) if len(sys.argv) > 6 else None
os.environ["QWIKI_LLM_URL"] = url
os.environ["QWIKI_CHAT_MODEL"] = model
for p in (ROOT, ROOT.parent / "common"):
    sys.path.insert(0, str(p))

from qwiki import config  # noqa: E402
from qwiki.embed import lm_studio_embeddings  # noqa: E402
from qwiki.evaluate import build_indexes, load_set, run_system, summarise_run, write_rows  # noqa: E402
from qwiki.llm import Chat  # noqa: E402

out = ROOT / out_name
llm = Chat()
if not llm.available():
    sys.exit("The chat server is not reachable at %s" % url)
try:
    cards, struct, naive = build_indexes(lm_studio_embeddings(config.PARSED / "embeddings.json"))
except Exception as e:  # an uncached text would need an embedding server
    sys.exit("Embedding cache incomplete or no embedding server: %s: %s" % (type(e).__name__, str(e)[:200]))
rows = []
for system in systems.split(","):
    for set_name in sets.split(","):
        res = run_system(system, set_name, load_set(set_name), cards, struct, naive, llm, out, limit=limit, log=print)
        rows += summarise_run(system, set_name, res)
        s = [r for r in rows if r["system"] == system and r["set"] == set_name and r["kind"] == "all"][0]
        print("%s on %s: accuracy %.3f, model-free %.2f, %.1f s/question"
              % (system, set_name, s["accuracy"], s["model_free_share"], s["seconds_per_q"]))
        write_rows(rows, out / "answers_summary.csv")
print("wrote", out / "answers_summary.csv")
