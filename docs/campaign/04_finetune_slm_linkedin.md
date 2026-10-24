# Post 4: fine-tuning on a CPU (DRAFT)

Facts behind this post: `code/finetune-slm/README.md` (Part 1 evaluation 2026-10-21; Part 2 results in
`code/finetune-slm/TODO.md`).

## Post

Can you fine-tune a language model on a laptop with no GPU? I wanted a real answer, so I tried it twice.

First, a tiny job. A 135-million-parameter model had to sort short messages into six categories, the kind of router that sits in front of a helpline. Out of the box it was close to guessing. With LoRA, which trains less than one percent of the weights, it learned the job on a plain laptop CPU, and it then needed a much shorter prompt than the "show it some examples" approach. For narrow, repetitive tasks, a small tuned model is a frugal choice.

Then a harder question. Can a 1-billion-parameter model learn a whole Marathi book, Sahaj Jeevan, well enough to answer questions about it with no lookup?

Mostly, no. Tuning roughly doubled its score over the untouched model, but it learned the practice questions far better than the book itself. The plain approach won clearly: keep the base model, look up the right passage, let the model read it.

I wrote my prediction down before measuring, and it held. Fine-tuning teaches style and narrow skills. Facts belong in retrieval.

Both experiments run on ordinary hardware, with the data, the code and the honest scores in the repo.

Open threads for anyone who wants them: a Qwen3 comparison, quantising the tuned model for a phone, and more Marathi and Hindi tasks. Good material for an internship or a research paper on Indian-language small models.

github.com/yogeshhk/FrugalAI (code/finetune-slm)

#FrugalAI #FineTuning #LoRA #Marathi

## Banner
Title: "Teach it small"
Scene: A small brass lamp-shaped robot sitting at a low wooden desk with a Marathi book open, a laptop with a fan
sticker beside it, a few labelled envelopes sorted into six slots of a wooden letter rack.
Alt text: Hand-drawn illustration of a small robot studying a Marathi book next to a letter rack with six slots,
titled "Teach it small".
