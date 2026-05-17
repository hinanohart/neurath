# Security Policy

## Reporting

Please report suspected vulnerabilities by opening a
[private security advisory](https://github.com/hinanohart/neurath/security/advisories/new)
on GitHub. Do **not** open a public issue for security problems.

I'll acknowledge receipt within 7 days and aim to publish a fix or
workaround within 30 days, depending on severity.

## Scope

- The neurath library itself (the `neurath` package).
- The release build pipeline (`.github/workflows/release.yml`).

Out of scope:

- Third-party dependencies (LiteLLM, pydantic, networkx, PyYAML) — please
  report those to their respective maintainers.
- Vulnerabilities in any LLM provider that LiteLLM dispatches to.

## Supported versions

Only the latest release line (currently 0.1.x) is supported. Older releases
are advisory-only.
