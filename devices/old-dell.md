# Old Dell laptop (CPU-only Linux)

Status: setup notes only. No benchmark has been run on this machine yet.

## Hardware to record before benchmarking
Fill in from `lscpu`, `free -h` and `lsblk -d -o NAME,ROTA` (ROTA 0 means SSD). The AIOOLL repository's
README reports an Intel i3-8130U, 8 GB RAM and an SSD for its own numbers; confirm this is the same
machine before reusing that description.

| Item | Value |
|------|-------|
| Model | to fill in |
| CPU, physical cores / threads | to fill in |
| RAM | to fill in |
| Storage (SSD or HDD) | to fill in |
| OS and version | to fill in |

## Setup checklist
Adapted from the hardware guide in [AIOOLL](https://github.com/yogeshhk/AIOOLL) (MIT), keeping the steps and
dropping its unsourced speed-up percentages. Measure each change yourself.

1. Install a light desktop (for example Xubuntu) or run headless, so more RAM is free for the model.
2. Install Ollama, then pull a small model, for example `ollama pull qwen3:1.7b`.
3. CPU governor to performance: `echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`.
4. Threads: for hyper-threaded CPUs try the physical core count rather than all threads, and compare.
5. Close the browser and other heavy programs; keep at least 2 GB of RAM free (see `free -h`).
6. Watch temperature (`sensors`, from the `lm-sensors` package) during a run, since laptops throttle.
7. Prefer an SSD. If the model must use swap on an HDD, pick a smaller model instead.

## Run the benchmark
```bash
conda env create -f environment.yml && conda activate frugalai
cd harness
python -m frugalai_harness.bench --backend ollama --model qwen3:1.7b --device old-dell --quantisation Q4_K_M
```
Then run the wiki recipe the same way with `--backend ollama` and commit the CSV. Follow
[benchmarks/METHODOLOGY.md](../benchmarks/METHODOLOGY.md).
