"""LBS record schema. Runtime is a lookup; this only validates authored/Astra JSON."""
from __future__ import annotations

MX = (
    "term_substitution",
    "condition_omission",
    "relationship_reversal",
    "scope_error",
    "surface_feature_capture",
    "mechanism_conflation",
    "operation_confusion",
)
LETTERS = ("A", "B", "C", "D")


def validate_followup(fu: dict) -> list[str]:
    err = []
    if not isinstance(fu, dict):
        return ["followup is not an object"]
    if not str(fu.get("stem") or "").strip():
        err.append("followup.stem empty")
    opts = fu.get("options") or {}
    if not isinstance(opts, dict):
        err.append("followup.options missing")
    else:
        for k in LETTERS:
            if not str(opts.get(k) or "").strip():
                err.append(f"followup.options.{k} empty")
    key = str(fu.get("key") or "").strip().upper()
    if key not in LETTERS:
        err.append("followup.key not A–D")
    if not str(fu.get("why") or "").strip():
        err.append("followup.why empty")
    return err


def validate_item(uid: str, rec: dict, *, key: str | None = None) -> list[str]:
    err = []
    if not isinstance(rec, dict):
        return [f"{uid}: not an object"]
    if not str(rec.get("solve") or "").strip():
        err.append(f"{uid}: solve empty")
    wrong = rec.get("wrong") or {}
    if not isinstance(wrong, dict):
        err.append(f"{uid}: wrong missing")
        return err
    expected = [L for L in LETTERS if key is None or L != key]
    if key and set(wrong) != set(expected):
        err.append(f"{uid}: wrong letters {sorted(wrong)} != {expected}")
    elif not key and len(wrong) != 3:
        err.append(f"{uid}: expected 3 wrong options, got {sorted(wrong)}")
    for lab, row in wrong.items():
        if lab not in LETTERS:
            err.append(f"{uid}: bad letter {lab}")
            continue
        if key and lab == key:
            err.append(f"{uid}: wrong includes the key {key}")
        if not isinstance(row, dict):
            err.append(f"{uid}.{lab}: not an object")
            continue
        if row.get("mx_type") not in MX:
            err.append(f"{uid}.{lab}: mx_type {row.get('mx_type')!r}")
        if not str(row.get("pathway") or "").strip():
            err.append(f"{uid}.{lab}: pathway empty")
        err.extend(f"{uid}.{lab}: {e}" for e in validate_followup(row.get("followup") or {}))
    return err
