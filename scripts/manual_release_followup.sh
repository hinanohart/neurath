#!/usr/bin/env bash
# scripts/manual_release_followup.sh
#
# Single script that captures every step of the neurath release pipeline that
# CANNOT be done by an LLM agent on its own. Run interactively when you are
# ready to promote 0.1.x out of "GitHub-Releases-only" distribution.
#
# Author: hinanohart (2026-05-18)
# License: Apache-2.0 (same as the project)
#
# Usage:
#   bash scripts/manual_release_followup.sh           # prints the checklist
#   bash scripts/manual_release_followup.sh --check   # verifies what is and
#                                                     # is not yet done
#
# Nothing in this script writes secrets to disk or to the shell history.
# All authentication happens in a browser (PyPI UI) or via `gh` already
# authenticated on your machine.

set -euo pipefail

REPO="hinanohart/neurath"
PYPI_PROJECT="neurath"
LATEST_TAG="$(gh release view --repo "$REPO" --json tagName --jq .tagName 2>/dev/null || echo 'v0.1.1')"

bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# STEP 1 — PyPI Trusted Publisher (one-time, manual browser action)
# ---------------------------------------------------------------------------
step_pypi_trusted_publisher() {
  bold "STEP 1 — Configure PyPI Trusted Publisher (one-time)"
  cat <<EOF

This is the ONLY step that requires you to leave the terminal. It is a
browser-only flow because PyPI deliberately does not expose an API for
adding Trusted Publishers — the whole point is that the credential never
exists as a token.

  1. Open  https://pypi.org/manage/account/publishing/
  2. Sign in if needed.
  3. Click "Add a new pending publisher" if the project does not exist on
     PyPI yet, otherwise navigate to the existing $PYPI_PROJECT project and
     pick "Add a new publisher" inside it.
  4. Fill in:
       PyPI project name:       $PYPI_PROJECT
       Owner:                   hinanohart
       Repository name:         neurath
       Workflow filename:       release.yml
       Environment name:        pypi
  5. Save.

Then run:

  gh variable set PYPI_TRUSTED_PUBLISHER --body true --repo $REPO

so that the \`if: \${{ vars.PYPI_TRUSTED_PUBLISHER == 'true' }}\` gate in
release.yml opens for the next tag. (We deliberately gate via a repo
variable rather than always-on so that a half-configured Trusted Publisher
cannot cause a publish to fail mid-release.)

EOF
}

# ---------------------------------------------------------------------------
# STEP 2 — Cut the first PyPI-published patch (v0.1.2 or whatever is next)
# ---------------------------------------------------------------------------
step_first_pypi_publish() {
  bold "STEP 2 — Cut the first PyPI-published patch"
  cat <<EOF

Once Step 1 is done, the next tag will be picked up by release.yml and the
pypi_publish job will run automatically. To exercise it without changing
behavior, bump pyproject.toml to v0.1.2 with a one-line CHANGELOG entry
("first PyPI-published tag"), then:

  git tag -a v0.1.2 -m "neurath v0.1.2 (first PyPI publish)"
  git push origin v0.1.2

The CI run will appear at:
  https://github.com/$REPO/actions

And once green, the release at:
  https://pypi.org/project/$PYPI_PROJECT/

If pypi_publish FAILS but github_release succeeds, you must NOT delete the
tag — re-cut a fresh patch (v0.1.3). PyPI never lets the same version
re-upload, even if the previous upload failed midway.

EOF
}

# ---------------------------------------------------------------------------
# STEP 3 — Hase et al. 2026 numerical replication (LLM budget required)
# ---------------------------------------------------------------------------
step_hase_replication() {
  bold "STEP 3 — Hase et al. 2024 numerical replication (deferred from v0.1)"
  cat <<EOF

The benchmark harness at benchmark/runner.py runs end-to-end but the
numbers have not been compared to the paper. To execute:

  1. Fetch the dataset from peterbhase/LLM-belief-revision into ./data/
     (we do not bundle it for licence reasons).
  2. Set an LLM API key in your shell with \`!\`-prefix or env-only — do
     NOT cat the key or echo it. e.g. shell history-free:
         read -s OPENAI_API_KEY && export OPENAI_API_KEY
  3. Run (budget: a few US dollars for gpt-4o-mini on 50 cases):
         python -m benchmark.runner \\
             --dataset data/hase2024.jsonl \\
             --model gpt-4o-mini \\
             --num-cases 50 \\
             --seed 0
  4. Commit the resulting JSON under benchmark/results/ and reference its
     mean_accuracy in the README "What is verified" list. ONLY then can
     "Hase 2024 numerical replication" be promoted out of the README's
     "Engineering limitations" section.

EOF
}

# ---------------------------------------------------------------------------
# STEP 4 — VCR cassettes for LLM-touching tests
# ---------------------------------------------------------------------------
step_vcr_cassettes() {
  bold "STEP 4 — VCR cassettes for LLMTranslator tests"
  cat <<EOF

The dev extra already pulls in \`vcrpy\`. The pattern is:

  1. Create benchmark/cassettes/ (already gitignored under benchmark/cache/
     if you prefer — adjust the .gitignore if you want them tracked).
  2. Add a fixture that, under \`record_mode='once'\`, captures a real LLM
     response while the API key is in env, and then re-uses the cassette
     for every subsequent run.
  3. Redact the \`Authorization\` and \`X-API-Key\` headers in the
     cassette factory (vcrpy supports this declaratively).
  4. Wire CI to pass without a network egress by setting
     VCR_RECORD_MODE=none in the test job.

Until this is done, LLMTranslator tests rely on an injected completion_fn
and never exercise the real LiteLLM path.

EOF
}

# ---------------------------------------------------------------------------
# STEP 5 — 30/90 day adoption review
# ---------------------------------------------------------------------------
step_adoption_review() {
  bold "STEP 5 — 30 and 90 day adoption review (calendar reminders)"
  cat <<EOF

The state file at .neurath-pipeline-state.yaml splits success metrics into
release_dod (machine-checkable at tag time) and adoption_30d / adoption_90d
(evaluated post-tag). Mark in your own calendar:

  v0.1.1 + 30 days  =  2026-06-17  →  check: any external issues filed?
  v0.1.1 + 90 days  =  2026-08-16  →  check: 5 issues / benchmark reproduced
                                              by anyone / PyPI live?

If none of those are met, the project should be honestly reframed in the
README rather than padding the metrics. The current "Status — scaffold
release" framing tolerates zero external adoption gracefully.

EOF
}

# ---------------------------------------------------------------------------
# --check mode — verify current state of each manual step
# ---------------------------------------------------------------------------
check_state() {
  bold "Current state of manual followup items (read-only):"
  echo

  printf '  PyPI Trusted Publisher gate:        '
  if gh variable list --repo "$REPO" 2>/dev/null | grep -q PYPI_TRUSTED_PUBLISHER; then
    green "PYPI_TRUSTED_PUBLISHER variable is set"
  else
    yellow "not set yet — pypi_publish will skip on next tag"
  fi

  printf '  Latest tag:                         '
  green "$LATEST_TAG"

  printf '  Release assets:                     '
  gh release view "$LATEST_TAG" --repo "$REPO" --json assets --jq '.assets[].name' 2>/dev/null \
    | paste -sd, - || red "could not fetch release"

  printf '  PyPI project visible:               '
  if curl -sf -o /dev/null "https://pypi.org/pypi/$PYPI_PROJECT/json"; then
    green "yes"
  else
    yellow "no — install via GitHub Release wheel for now"
  fi

  printf '  Hase 2024 results committed:        '
  if [ -d benchmark/results ] && [ -n "$(ls -A benchmark/results 2>/dev/null)" ]; then
    green "yes"
  else
    yellow "no — STEP 3 still open"
  fi

  printf '  VCR cassettes committed:            '
  if [ -d benchmark/cassettes ] && [ -n "$(ls -A benchmark/cassettes 2>/dev/null)" ]; then
    green "yes"
  else
    yellow "no — STEP 4 still open"
  fi
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
case "${1:-help}" in
  --check)
    check_state
    ;;
  help|*)
    cat <<EOF
neurath manual followup script

This script does NOT modify anything. It only prints the steps that an
LLM agent cannot perform on its own and reports the current state.

Usage:
  bash $0           print the full checklist (STEP 1..5)
  bash $0 --check   read-only status of each manual step

EOF
    step_pypi_trusted_publisher
    step_first_pypi_publish
    step_hase_replication
    step_vcr_cassettes
    step_adoption_review
    ;;
esac
