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

The runner computes a SHA-256 of the dataset file and embeds it in each
results JSON (`dataset_sha256` field) so a reproduction attempt can verify
that exactly the same bytes were used. There is no committed
`benchmark/datasets.lock` file at release time — the hash is captured in the
results artifact on each run.
