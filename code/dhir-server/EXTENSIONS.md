# Extensions: dhir-server

Dhir 2B run from its GGUF file with ZenteiQ's `llama-server` (LM Studio cannot load it). Ideas for anyone who forks
this repo. Pick one, open an issue so two people do not do the same, and send a pull request. Rules: never invent a
number, name the device and quantisation, and read a model card before quoting it. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## Raspberry Pi 5 or other ARM board (medium)
- Build the `dhir-support` branch of llama.cpp on the board, load `Dhir-2B-Q4_K_M.gguf` and log a benchmark row with `python -m frugalai_common.bench --ram-port <port>`. The Pi 3 has 1 GB RAM and cannot hold the file.
- Needs: the board. Report build problems; they are results.

## Thread settings (small)
- The card suggests `-t` equal to performance cores. Every run so far used `-t 8` on an i7-1255U. Try other values with the benchmark runner and report the best and the spread.

## Dhir 5B-A1.7B (medium)
- Listed on the card as stronger and faster than 2B on a CPU. Read its card, run `rag_check.py` and the benchmark, and add a row.

## Q4 against Q8 on your device (small)
- The author kept Q8_0 on one laptop. On your device compare both for speed, memory and the tool round trips described in the README.

## Tool round trips in a client (small)
- The README tip (wrap a plain-text tool result as JSON and leave the tools out of that turn) rests on a handful of trials. Put it in a small helper next to `frugalai_common.llm`, with tests, and measure it on more tools and prompts.

## A thin server for safety limits (small)
- llama-server has no `max_tokens` cap or host-name check. If you expose it beyond one machine, add them in a small proxy and say what you tested. The removed wrapper did this; it is in the Git history.

## LM Studio support (small, wait for upstream)
- When the Dhir architecture reaches mainline llama.cpp and an LM Studio runtime, retry loading the GGUF there and compare one probe with llama-server. Do not relabel the GGUF to force a load: the tokenisation would change.

## More languages in the check (medium)
- `rag_check.py` uses English questions from wiki-rag. Add Hindi and Marathi questions you wrote, with a native reader to review the answers.

## Compare with other Indic small models (medium)
- Same prompts and benchmark against another small multilingual model served the same way; report speed, memory and the check scores in one table.
