"""Prompts used by the LLM Adapter.

Kept separate from the adapter so prompt versions can be pinned and diffed
independently from code changes.
"""

CLAIM_TO_TRUTH_SYSTEM = """\
You are an epistemic estimator. The user will give you a single claim and \
optional supporting context. Respond ONLY with a JSON object of the form:

  {"frequency": <float in [0,1]>, "confidence": <float in [0,1)>, \
"justification": <one-sentence reason>}

`frequency` is your estimate of how often the claim would be true, were it \
checked many times against reality. `confidence` is how much evidence you \
have to support that frequency estimate; confidence 0 means you have no \
information at all (frequency should then be 0.5). Confidence must be \
strictly less than 1 — perfect certainty is not allowed; a strong belief \
should report e.g. 0.99, never 1.0.

Example for a strong but not-quite-certain claim:
  {"frequency": 0.97, "confidence": 0.85, "justification": "..."}
"""

CLAIM_TO_TRUTH_USER_TEMPLATE = """\
Claim: {claim}

Context: {context}

Return only the JSON object.
"""


def claim_to_truth_messages(claim: str, context: str | None) -> list[dict[str, str]]:
    """Build the chat messages for a claim → truth-value estimation."""
    return [
        {"role": "system", "content": CLAIM_TO_TRUTH_SYSTEM},
        {
            "role": "user",
            "content": CLAIM_TO_TRUTH_USER_TEMPLATE.format(
                claim=claim,
                context=context if context else "(none)",
            ),
        },
    ]
