# Limits and workarounds

Where small models fall short, and what to do about it. Every row comes from our own runs (one machine, small samples:
read as hints, not rules). Sources of the runs: `code/workflow-agent/README.md`, `code/dhir-server/README.md`,
`code/common/benchmarks/results/`.

| Limit seen | Evidence | What to do |
|------------|----------|------------|
| Gemma 2 2B never called a tool through the standard interface | 0 of 5 tries, 2026-10-19 | Use a model that does: Qwen3 1.7B called it 5 of 5; Dhir 2B called a tool when asked (2026-11-14). Or use a text ReAct loop, where the model writes an Action line and code runs the tool. Test your own model. |
| Wrong number comparison ("10.2 is higher than 11.4") | 5 of 5 tries, stub data | Let code compare; the model only words the result (right in 5 of 5). |
| Two-city comparison wrong with a text ReAct agent | 5 of 5 wrong | Use a fixed workflow: code decides the steps, the model words the answer (5 of 5 right). |
| Hidden thinking uses the token budget | Qwen3 1.7B spent 126 of 128 tokens | Turn thinking off (`/no_think` for Qwen3) or raise the budget. Dhir has no such switch. |
| Dhir 2B calls the same tool again after a tool result | Q4_K_M after every result, 2026-11-14 | Wrap the result as JSON and leave the tools out of that one turn. A handful of trials only. |
| Reworded questions are missed by keyword retrieval | 34 percent right on paraphrases, every model | Add embeddings or a hybrid retriever; compare them, do not assume the hybrid wins. |
| Evidence is thin | one machine, one day; nothing evaluated on real Hindi or Marathi speech | Repeat on your own device and report the median and range. |
