# TODO

All projects are built and measured. The offline Frugal AI demo is ready for the Dec 12 talk; parked for later are the `app_faq.py` page and the Marathi fine-tune rerun (`code/demo/TODO.md`) and voice-form (`code/voice-form/TODO.md`). One open item: trying the Indian model Dhir 2B in the other projects through the new local server (`code/dhir-server/TODO.md`; built and tested, answer quality not measured yet). Tests: `python -m pytest code -q` (313 pass, 20 skipped; the skips need private data that is not set on this machine). Python: conda env `genai`
(the `frugalai` env from `environment.yml` was never built). LM Studio is stopped on purpose; start it only when a task needs it.
