# TODO (quantum-wiki)

Built and measured on 2026-10-20; see README.md for results. Closed on 2026-10-21: nothing is open. Ideas that were
considered and not planned are in the root `TODO.md` under "Future ideas".

## Done
- [x] Source and scope confirmed: the 39-page curriculum PDF, pages 14 (Table of Courses) and 16 to 37 only; the
      opening material and the Hindi pages are excluded.
- [x] Docling parse, with the table's spanning rows and the list hierarchy (from indentation); parsing is one-time
      and cached.
- [x] Course cards, status groups, topic trees, outcomes, references, lecture counts; 23 offline tests.
- [x] LangChain 1.x retrieval over structure-aware chunks (dense, BM25, hybrid); the dense variant wins on this PDF.
- [x] Router and deterministic tools, the code check on course codes, and the vocabulary gate as an optional flag.
- [x] Evaluation: 80 tuned questions, 30 held-out questions, three systems, retrieval comparison.
- [x] Grounding check (`ungrounded_names` in `qwiki/scoring.py`, used by `answer_agent`): written and tested offline;
      its effect on model answers was not measured.

## Risks and notes
- The router is rules, so it needs maintenance when question shapes change; every failure should become a test.
- Docling downloads its models into `models/` (about 300 MB, git-ignored); the first parse needs network access.
- The held-out set is no longer pristine (see README), and both question sets were drafted by Claude and not reviewed.
