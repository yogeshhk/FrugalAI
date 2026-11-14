# TODO (dhir-server)

Optional; nothing here is needed for the Dec 12 talk. Open actions only. The GGUF route works (README, "Run it").

- [ ] LM Studio: it still cannot load the Dhir GGUF (architecture `dhir` and its tokenizer mode exist only in ZenteiQ's `dhir-support` llama.cpp branch). Watch for the upstream llama.cpp merge and a later LM Studio runtime, then retry loading the GGUF there and compare one probe run with llama-server. Do not relabel the GGUF to force a load: the tokenisation would change.
- [ ] Thread settings: the model card suggests `-t` = performance cores and `-tb` = all cores. The i7-1255U has 2 performance and 8 efficiency cores; all runs so far used `-t 8`. Try other `-t` values with the benchmark runner before changing the advice.
- [ ] Dhir 5B-A1.7B GGUF (3.4 GB at Q4_K_M) is listed on the card as stronger and faster than the 2B on a CPU. Read its own card first, then run `rag_check.py` and the benchmark if it fits the use.
- [ ] Raspberry Pi 5 (only if bought; the Pi 3 has 1 GB and cannot hold the 1.3 GB file): build the `dhir-support` branch on the Pi and log a benchmark row for Q4_K_M.
- [ ] Read ZenteiQ's technical report when it is published and add it to `docs/sources.md` before quoting any of its numbers.
