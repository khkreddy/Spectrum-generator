#!/usr/bin/env python3
"""Astra harness: author learn-by-solve follow-ups for 9701 spectroscopy MCQs.

Offline. Runtime never calls a model — it looks up the JSON this writes.

  PYTHONPATH=src .venv/bin/python src/ask_astra_lbs.py --missing
  PYTHONPATH=src .venv/bin/python src/ask_astra_lbs.py --uid 9701_m19_qp_12:q30
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARVEST = Path("/home/harik/awm_build/data/spectra")
if not HARVEST.is_dir():
    HARVEST = ROOT.parent  # Spectrum-generator checkout has no harvest tree
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "practice"))
from astra_client import ask, extract_json  # noqa: E402
from lbs_schema import LETTERS, MX, validate_item  # noqa: E402

QUEST = ROOT / "review" / "static" / "questions.json"
MS_KEYS = ROOT / "practice" / "static" / "ms_keys.json"
LBS_PY = ROOT / "practice" / "static" / "lbs.json"
OUT = ROOT / "out" / "astra"

PROMPT = """You are Astra. Cognitive task only: write a learn-by-solve follow-up pack for ONE Cambridge 9701 spectroscopy MCQ.

Runtime is a JSON lookup. You author once. Do not chat. Do not ask questions.

Mark-scheme key: {key}

Stem:
{stem}

Options:
A. {optA}
B. {optB}
C. {optC}
D. {optD}

Examiner comment (may be empty):
{comment}

The original exam figure is attached when present. Use it. Do not invent peaks that are not on the figure or in the stem.

A follow-up is a SMALLER four-option MCQ that isolates the mistake behind ONE wrong letter. The student never sees mx_type. Do not leak the original key in the follow-up stem.

mx_type must be exactly one of:
- term_substitution — swapped one named entity for another (C=C for C=O, Cl for Br, …)
- condition_omission — used one required feature and dropped another
- relationship_reversal — swapped cause/effect, reactant/product, major/minor
- scope_error — over- or under-extended a correct rule
- surface_feature_capture — grabbed a memorable number or a fingerprint wiggle
- mechanism_conflation — mixed two reactions / two spectroscopies
- operation_confusion — arithmetic, counting, isotope-ratio, or formula error

Return ONE JSON object, no markdown:
{{
  "uid": "{uid}",
  "solve": "one paragraph: how to read the evidence to the key",
  "wrong": {{
    "X": {{
      "mx_type": "...",
      "pathway": "what the student who picked X actually did",
      "followup": {{
        "stem": "...",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "key": "A",
        "why": "one sentence after they answer the follow-up"
      }}
    }}
  }}
}}

wrong must contain the three letters that are NOT the mark-scheme key, and only those.
Follow-up options must be four distinct, chemically true-or-false statements, one of them correct.
"""


def _ms_lookup(uid: str, ms: dict) -> str | None:
    m = re.match(r"^(9701_[msw]\d{2}_qp_\d+):q(\d+)$", uid)
    if not m:
        return None
    return (ms.get("papers") or {}).get(m.group(1), {}).get(m.group(2))


def _png(folder: str) -> Path | None:
    p = HARVEST / "items" / folder / "original.png"
    return p if p.is_file() else None


def payload(row: dict, key: str) -> dict:
    opts = row.get("options") or {}
    return {
        "uid": row["uid"],
        "key": key,
        "stem": row.get("stem") or "",
        "optA": opts.get("A") or "",
        "optB": opts.get("B") or "",
        "optC": opts.get("C") or "",
        "optD": opts.get("D") or "",
        "comment": row.get("examiner_comment") or "",
        "folder": row.get("folder") or "",
    }


def run_one(item: dict, *, effort: str) -> dict:
    uid = item["uid"]
    prompt = PROMPT.format(**item)
    images = []
    png = _png(item["folder"])
    if png:
        images.append(png)
    safe = uid.replace(":", "_")
    text = ask(prompt, images=images or None, effort=effort, name=f"lbs_{safe}")
    obj = extract_json(text)
    if not isinstance(obj, dict):
        raise ValueError("Astra did not return an object")
    obj["uid"] = uid
    obj["source"] = "astra"
    obj["key"] = item["key"]
    err = validate_item(uid, obj, key=item["key"])
    if err:
        raise ValueError("; ".join(err))
    dest = OUT / f"lbs_{safe}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return obj


def missing_uids(quest: dict, ms: dict, lbs: dict) -> list[str]:
    have = set((lbs.get("items") or {}))
    out = []
    for row in quest.get("items") or []:
        if row.get("item_type") not in {"mcq", "mcq_diagram", "mcq_table", "three_statement"}:
            continue
        opts = row.get("options") or {}
        if sum(1 for k in LETTERS if opts.get(k) is not None) < 4:
            continue
        key = row.get("key") or _ms_lookup(row["uid"], ms)
        if not key:
            continue
        if row["uid"] not in have:
            out.append(row["uid"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uid", action="append", default=[])
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--effort", default="high")
    args = ap.parse_args()
    quest = json.loads(QUEST.read_text(encoding="utf-8"))
    ms = json.loads(MS_KEYS.read_text(encoding="utf-8")) if MS_KEYS.is_file() else {"papers": {}}
    lbs = json.loads(LBS_PY.read_text(encoding="utf-8")) if LBS_PY.is_file() else {"items": {}}
    by = {r["uid"]: r for r in quest.get("items") or []}
    uids = list(args.uid)
    if args.missing:
        uids.extend(missing_uids(quest, ms, lbs))
    # unique, stable
    seen = set()
    todo = []
    for u in uids:
        if u not in seen:
            seen.add(u)
            todo.append(u)
    if not todo:
        print("nothing to author")
        return 0
    print(f"Astra LBS harness n={len(todo)}", flush=True)
    ok = fail = 0
    for uid in todo:
        row = by.get(uid)
        if not row:
            print("SKIP unknown", uid, flush=True)
            fail += 1
            continue
        key = row.get("key") or _ms_lookup(uid, ms)
        if not key:
            print("SKIP no key", uid, flush=True)
            fail += 1
            continue
        try:
            run_one(payload(row, key), effort=args.effort)
            print("OK", uid, flush=True)
            ok += 1
        except Exception as e:
            print("FAIL", uid, e, flush=True)
            fail += 1
    print(f"done ok={ok} fail={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
