# Concepts

Short definitions used across the repo. Each term links to the sources entry that supports it.

## Frugal AI
Getting the most useful outcome from the least compute, money, energy and data. The Frugal AI Hub glossary
defines it as an approach that "maximizes environmental and societal impact with minimal resources"
([S1](sources.md#s1)).

## Small language model (SLM)
A language model small enough to run on a laptop, single-board computer or phone. This repo works mainly
with models of roughly 0.5B to 4B parameters. The exact models used are recorded with each benchmark result,
not assumed here.

## Quantisation
Storing model weights in fewer bits (for example 4-bit instead of 16-bit) to cut memory and speed up CPU
inference, at some cost in quality. GGUF is the file format used by llama.cpp, Ollama and LM Studio.
Typical names such as `Q4_K_M` describe the scheme. How much quality is lost depends on the model and task,
so this repo measures it per recipe and does not assume it.

## Knowledge distillation
Training a small "student" model to imitate a larger "teacher". Example from the literature: MoScNet, which
transliterates Modi script to Devanagari; the authors report a student about 163 times smaller in parameters
than its teacher that outperforms it ([S4](sources.md#s4)). That is the authors' claim on their dataset, not
a general rule.

## Pruning
Removing weights or structures that contribute little, to shrink a model. Mentioned for completeness; not a
focus of the first milestones.

## Retrieval-augmented generation (RAG)
Answering from a local document collection: split documents into chunks, embed them, store the vectors,
retrieve the closest chunks for a question, and give them to the model with the question. Lets a small model
answer from a large private corpus without retraining.

## Token and context window
A token is the unit of text a language model reads and writes (a word, part of a word or a symbol). The
context window is the amount of text, in tokens, the model can take into account at once. Token counts
matter for cost, speed and memory; the link to energy is to be measured here, see
[token_frugality.md](token_frugality.md). Sarvam reports Indian-language text needs more tokens for the same
question ([S3](sources.md#s3)).

## KV cache
Keys and values stored for tokens already processed, so the model need not recompute them for each new
token. It takes memory per request and grows with context length ([S16](sources.md#s16)).

## Speculative decoding, mixture of experts, state space models
Short definitions with the sourced figures are in [token_frugality.md](token_frugality.md)
([S15](sources.md#s15), [S18](sources.md#s18), [S17](sources.md#s17)).

## Frozen encoder plus small head (probe)
A large model (the encoder) is trained once and then kept frozen, so its weights do not change. A small
part is trained on top of its outputs for one task: a linear layer (a "linear probe") or a small attention
block (an "attentive probe"). Papers use this to evaluate how good the encoder's representations are
([S20](sources.md#s20), [S21](sources.md#s21)). Why it may suit frugal work: only the small head needs
training data and compute. The encoder itself still has to be run at inference, so it is not free on small
hardware (to measure).

## JEPA
Joint-Embedding Predictive Architecture: a self-supervised method that learns by predicting the
representation of hidden parts of an input from the visible parts, instead of predicting pixels. Examples
fetched for this repo: I-JEPA for images ([S19](sources.md#s19)), V-JEPA 2 for video ([S20](sources.md#s20))
and LeJEPA, a training objective with a theory for it ([S21](sources.md#s21)). Whether this is the model
family the repo owner remembered as "Jave" is an inference, see [landscape.md](landscape.md).

## Edge and offline
Running where the data is, without needing the internet at run time. The point is privacy, latency, cost and
resilience, not only speed.

## Runtimes used here
- Ollama and LM Studio: local servers that run GGUF models (both are built on llama.cpp-style runtimes).
- llama.cpp: the underlying CPU inference engine.
- Others to evaluate later: ONNX Runtime, LiteRT (the successor to TensorFlow Lite) for phones.
