# TODO (dhir-server)

Parked to 2027; optional, nothing here is needed for the Dec 12 talk. Open actions only. Run the server first (README, "Run it"); the model folder is `C:\Users\yoges\Downloads\dhir-2b`.

- [ ] GGUF: ZenteiQ replied that a GGUF build goes on AIKosh (after IndiaAI approval), and that more quantised versions and a detailed technical report follow on Hugging Face. The author downloads the GGUF (AIKosh needs a login). Then: load it in LM Studio, check the answers match the Transformers server on a few prompts (tokenisation is the risk), run `python -m frugalai_common.bench` with `--repeats 3` and `rag_check.py` against LM Studio, and compare with the stored Transformers numbers in the README. If it holds up, make LM Studio the main route and keep this server as a fallback. Also read the Hugging Face technical report and add the model card and report to `docs/sources.md` before quoting anything from them.
