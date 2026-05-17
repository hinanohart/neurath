# Contributing to neurath

Thanks for considering a contribution. neurath is pre-alpha; the API will move.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,benchmark]"
pytest
ruff check . && ruff format --check . && mypy src/
```

## Style

- Python ≥ 3.11, `from __future__ import annotations` everywhere.
- `ruff format` is the formatter; `ruff check` is the linter.
- Public functions have docstrings explaining *why*, not *what*.
- Tests prefer Hypothesis property-based tests for algebraic properties.

## Pull requests

- One topic per PR.
- Update `CHANGELOG.md` under `[Unreleased]`.
- New behaviour comes with a test that fails before your change.
- CI (ruff + mypy + pytest on 3.11/3.12) must pass.

## Conduct

Be kind. Disagree on the work, not the person.

## License

By contributing you agree your contribution is licensed under Apache 2.0.
