# Benchmarks

`neurath` ships a runner harness for the
[Hase 2024 LLM-belief-revision dataset](https://github.com/peterbhase/LLM-belief-revision).

The harness is intentionally separated from the package proper: real LLM calls
cost money and require API keys, so the unit tests inject stubs and the
benchmark runs out-of-tree.

## Running

```bash
pip install -e ".[benchmark,dev]"
python -m benchmark.runner --model gpt-4o-mini --num-cases 50 --seed 0
```

Results land in `benchmark/results/<timestamp>.json` with:

- per-case accuracy
- mean ± bootstrap 95% CI accuracy
- the dataset hash (so you can verify reproduction)
- the LiteLLM model id and the prompt version

No SOTA claims are made: the goal is to publish reproducible baseline numbers
that other implementations can compare against.

## Dataset

We pin the dataset by commit hash. See `benchmark/datasets.lock` (created on
first run).
