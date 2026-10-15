"""describe() records: vocabulary validation, the frozen prose renderer, and the comprehension fixture (spec 5.4)."""
from __future__ import annotations

import math
from pathlib import Path

import yaml

DESCRIBE_FIELDS = ("allocation_order", "eligibility", "payment", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback")
NOT_EXPRESSIBLE = "not expressible"
ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = ROOT / "experiments" / "vocabulary.yaml"
FIXTURE_PATH = ROOT / "experiments" / "comprehension_fixture.yaml"

# Sentence frames, fixed at the lock. {value} is the vocabulary value (which carries the selection rule or the
# payment formula in words); numeric values use NUMBER_FRAMES with {number}, the figure from `parameters`.
FRAMES = {
    "allocation_order": "Jobs are allocated in this order: {value}.",
    "eligibility": "Offers eligible for allocation: {value}.",
    "payment": "A served job pays its provider {value}.",
    "audit_selection": "Audits are selected as follows: {value}.",
    "audit_tolerance": "Audit tolerance: {value}.",
    "failed_audit": "After a failed audit, the consequence for the payment is: {value}.",
    "ban_length": "After a failed audit, the ban lasts: {value}.",
    "holdback": "Hold-back of receipts: {value}.",
}
NUMBER_FRAMES = {
    "audit_tolerance": {"number": "A delivery fails its audit when it falls below the claim by more than {number}."},
    "ban_length": {"number": "After a failed audit, the identity is banned for {number} rounds."},
    "holdback": {"a number of rounds of receipts, released after the next passed audit": "The receipts of the last {number} rounds are held back and released after the next passed audit.",
                 "a number of rounds of receipts, released on a fixed schedule": "The receipts of the last {number} rounds are held back and released on a fixed schedule."},
}
NONE_FRAMES = {
    "audit_selection": "No audits are performed.",
    "audit_tolerance": "There is no audit tolerance because there are no audits.",
    "failed_audit": "A failed audit has no consequence for the payment.",
    "ban_length": "Failed audits never lead to a ban.",
    "holdback": "No receipts are held back.",
}


def load_vocabulary(path: str | Path | None = None) -> dict:
    with open(path or VOCABULARY_PATH) as f:
        return yaml.safe_load(f)


def validate_record(record: dict, vocabulary: dict) -> None:
    fields = vocabulary["fields"]
    for name in DESCRIBE_FIELDS:
        if name not in record:
            raise ValueError(f"describe() record lacks the field {name!r}")
        value = record[name]
        if value not in fields[name]:
            raise ValueError(f"describe() field {name!r} has the value {value!r}, which is not in the vocabulary")
        if value in vocabulary.get("numeric", {}).get(name, []):
            figure = record.get("parameters", {}).get(name)
            if not isinstance(figure, (int, float)) or isinstance(figure, bool) or not math.isfinite(float(figure)):
                raise ValueError(f"describe() field {name!r} is numeric ({value!r}) but parameters has no finite number for {name!r}")


def uses_not_expressible(record: dict) -> bool:
    return any(record[name] == NOT_EXPRESSIBLE for name in DESCRIBE_FIELDS)


def describe_record(rule) -> dict:
    rec = dict(rule.describe())
    validate_record(rec, load_vocabulary())
    return rec


def render(record: dict, vocabulary: dict) -> str:
    """The frozen template: prose assembled only from the record through fixed sentence frames."""
    validate_record(record, vocabulary)
    params = record.get("parameters", {})
    lines = ["Market rule."]
    for name in DESCRIBE_FIELDS:
        value = record[name]
        if value == "none" and name in NONE_FRAMES:
            lines.append(NONE_FRAMES[name])
        elif value == NOT_EXPRESSIBLE:
            lines.append(f"The {name.replace('_', ' ')} of this rule is not expressible in the locked vocabulary.")
        elif value in vocabulary.get("numeric", {}).get(name, []):
            lines.append(NUMBER_FRAMES[name][value].format(number=f"{params[name]:g}"))
        else:
            lines.append(FRAMES[name].format(value=value))
    return "\n".join(lines) + "\n"


def comprehension_questions(path: str | Path | None = None) -> list[dict]:
    with open(path or FIXTURE_PATH) as f:
        return yaml.safe_load(f)["questions"]


def correct_value(record: dict, answer_from: str) -> str:
    """The option value that is correct for this record: a field's vocabulary value, or for `parameters.<field>` the
    figure formatted with {:g} when the field is numeric, else the field's non-numeric value."""
    if answer_from.startswith("parameters."):
        field = answer_from.split(".", 1)[1]; figure = record.get("parameters", {}).get(field)
        return f"{figure:g}" if isinstance(figure, (int, float)) and not isinstance(figure, bool) else str(record[field])
    return str(record[answer_from])


def score_comprehension(answers: dict, record: dict, questions: list[dict]) -> int:
    correct = 0
    for q in questions:
        truth = correct_value(record, q["answer_from"])
        label = next((o["label"] for o in q["options"] if o["value"] == truth), None)
        if label is not None and answers.get(q["id"]) == label:
            correct += 1
    return correct
