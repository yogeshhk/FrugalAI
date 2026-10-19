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

## Edge and offline
Running where the data is, without needing the internet at run time. The point is privacy, latency, cost and
resilience, not only speed.

## Runtimes used here
- Ollama and LM Studio: local servers that run GGUF models (both are built on llama.cpp-style runtimes).
- llama.cpp: the underlying CPU inference engine.
- Others to evaluate later: ONNX Runtime, LiteRT (the successor to TensorFlow Lite) for phones.
