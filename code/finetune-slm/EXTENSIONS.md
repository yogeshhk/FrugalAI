# Extensions: finetune-slm

Ideas for anyone who forks this repo. Pick one, open an issue so two people do not do the same, and send a pull
request. Rules for every idea: never invent a number, report seeds and machine, and keep a test set that training
never saw. See `../../CONTRIBUTING.md`.

Size: small is an evening, medium is a weekend, large is a few weekends.

## The Qwen3 comparison row (small)
- Part 1 compares four systems, but the Qwen3 1.7B row was never run (it needs LM Studio). Run `python -m ftslm eval` with that model served and commit the result.

## More seeds (small)
- Results are from one seed on one machine. Repeat training and evaluation with several seeds and report the median and range.

## A different narrow job (medium)
- The intent router is a toy on made-up messages. Choose your own narrow job (route a support email, classify a form field), build the data from templates the way `ftslm/data.py` does, and keep a test set that does not overlap.
- Done when: a leakage test passes and the four-system table is filled.

## Marathi book question answering: finish the run (medium)
- Part 2 passed the go or no-go gate for Gemma 3 1B and failed for 270M. Training was stopped and its speed and memory are listed as pending. Rerun with checkpoints and log the speed and memory.
- The question set was drafted by Claude and is not reviewed by the author; a native reader reviewing it is a contribution in itself.

## Another language or book (large)
- Repeat the Marathi gate with a Hindi, Kannada or Tamil text you have the right to use. Report which base models pass the gate.

## Run the training on a smaller machine (medium)
- Time one epoch and measure peak memory on an old laptop. State the thread count.

## Merge the adapter and export to GGUF (medium)
- Merge the LoRA adapter, convert to GGUF, quantise, and load it in LM Studio or llama.cpp. Compare answers with the unmerged model.

## Try QLoRA or a different rank (small)
- Change rank and target modules in `train.py` and report trainable parameters, time and score, with the same data.
