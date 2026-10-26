# Results

Written by `python -m voiceform report` from results/*.summary.json. A row exists only if a
script produced it on the named device (see each summary file). Scripts drafted by Claude and not yet
reviewed by the author; dates resolve against eval/eval.yaml.

## Extraction (field accuracy)

| Lang | Route | Model | Condition | Set | Utterances | Field accuracy | To fix per utterance | All correct | Seconds per utterance | Date |
|---|---|---|---|---|---|---|---|---|---|---|
| hi | direct | gemma-2-2b-it | reference | tune | 18 | 0.984 | 0.17 | 15 | 56.85 | 2026-10-26 |
| hi | direct | gemma-2-2b-it | reference | heldout | 9 | 0.933 | 0.44 | 6 | 57.24 | 2026-10-26 |
| hi | direct | qwen/qwen3-1.7b | reference | tune | 18 | 0.919 | 0.83 | 10 | 53.14 | 2026-10-26 |
| hi | direct | qwen/qwen3-1.7b | reference | heldout | 9 | 0.950 | 0.44 | 5 | 10.17 | 2026-10-26 |
| hi | rules | none | reference | tune | 18 | 0.468 | 3.78 | 0 | 0.0 | 2026-10-26 |
| hi | rules | none | reference | heldout | 9 | 0.450 | 3.67 | 0 | 0.0 | 2026-10-26 |
| hi | translate | qwen/qwen3-1.7b | reference | tune | 18 | 0.516 | 3.44 | 0 | 100.46 | 2026-10-26 |
| mr | direct | gemma-2-2b-it | reference | tune | 18 | 0.936 | 0.44 | 13 | 49.48 | 2026-10-26 |
| mr | direct | gemma-2-2b-it | reference | heldout | 9 | 0.902 | 0.78 | 5 | 47.79 | 2026-10-26 |
| mr | direct | qwen/qwen3-1.7b | reference | tune | 18 | 0.872 | 1.06 | 6 | 30.77 | 2026-10-26 |
| mr | direct | qwen/qwen3-1.7b | reference | heldout | 9 | 0.918 | 0.89 | 4 | 9.71 | 2026-10-26 |
| mr | rules | none | reference | tune | 18 | 0.480 | 3.72 | 0 | 0.0 | 2026-10-26 |
| mr | rules | none | reference | heldout | 9 | 0.443 | 3.78 | 0 | 0.0 | 2026-10-26 |
| mr | translate | qwen/qwen3-1.7b | reference | tune | 18 | 0.496 | 3.5 | 0 | 51.97 | 2026-10-26 |

## Speech to text

| Lang | Backend | Condition | Set | Utterances | WER | CER | RTF | RAM after load (MB) | Date | Note |
|---|---|---|---|---|---|---|---|---|---|---|
