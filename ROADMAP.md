# Roadmap

Scope rule: software and deployment, not chip design or hardware acceleration. Use an existing runtime
(llama.cpp, Ollama, LM Studio, ONNX Runtime, LiteRT) and measure it.

## M1: Skeleton and one end-to-end demo
- Repo skeleton, concepts, landscape and sources notes with verified claims.
- Harness v0: Ollama and LM Studio backends, tokens/s and RAM helper.
- Recipe: offline wiki/RAG on a Markdown folder.
- Benchmark method, first measured results on the old Dell.

## M2: Raspberry Pi 5
- Device setup notes and the same recipe measured on the Pi, including power draw (with the electronics
  engineer).
- First "what runs where" table with at least two devices.

## M3: ASHA-worker assistant (Marathi, Hindi, English)
- Safety framing and refusal policy first, then an evaluation set, then the recipe.
- Model shortlist for the three languages, tested against the evaluation set.
- Decision support only. No deployment without domain review.

## M4: Phone track
- Android path (LiteRT or llama.cpp build), one recipe measured on a real phone.

## Later
- Modi script OCR recipe (MoScNet and a classical baseline, compared).
- More languages, with community partners and data-custody rules written first.
- Internship project list and a consulting/training offer built on the recipes.
