#!/usr/bin/env python3
"""Pack 9701 items with base64 originals, stripped stems, and LBS keys."""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from display import learner_options, learner_stem, options_are_figure  # noqa: E402
from lbs_followups import build as build_lbs  # noqa: E402

CANON = Path(__file__).resolve().parents[1]
HARVEST = Path("/home/harik/awm_build/data/spectra")
QUEST = CANON / "review" / "static" / "questions.json"
TTWIN = Path("/home/harik/TTwin/data/questions/chemistry-senior.json")
EXAM = CANON / "out" / "exam_luna"
OUT = CANON / "practice" / "static" / "pack.json"
TEMPLATES = CANON / "data" / "rules" / "exam_ir_templates.json"
LBS_OUT = CANON / "practice" / "static" / "lbs.json"
CURVES = CANON / "practice" / "static" / "ir_examples.json"


def _b64(folder: str) -> str | None:
    d = HARVEST / "items" / folder
    raw = d / "original.base64"
    png = d / "original.png"
    if raw.is_file():
        blob = raw.read_text(encoding="utf-8").strip().replace("\n", "")
        if blob.startswith("data:"):
            return blob
        return "data:image/png;base64," + blob
    if png.is_file():
        return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode("ascii")
    return None


def _export_examples() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from generate import generate  # noqa: E402
    from render_tikz import render_all  # noqa: E402

    mols = [
        ("propan-1-ol", "CCCO"),
        ("propan-2-ol", "CC(C)O"),
        ("ethanol", "CCO"),
        ("propanone", "CC(=O)C"),
        ("ethanoic acid", "CC(=O)O"),
        ("propanoic acid", "CCC(=O)O"),
        ("ethyl ethanoate", "CCOC(=O)C"),
        ("glycerol", "OCC(O)CO"),
    ]
    out = []
    for name, smi in mols:
        spec = generate(smi, name=name)
        tikz = render_all(spec)
        ir = spec.get("ir") or {}
        out.append(
            {
                "name": name,
                "smiles": spec["smiles"],
                "formula": spec["formula"],
                "family": ir.get("family"),
                "template": None,
                "tikz": tikz.get("ir"),
                "T1450": next((t for wn, t in (ir.get("curve") or []) if abs(wn - 1450) < 3), None),
            }
        )
    CURVES.write_text(json.dumps({"examples": out}, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    lbs_doc = build_lbs()
    q = json.loads(QUEST.read_text(encoding="utf-8"))
    tt = {}
    if TTWIN.is_file():
        for it in json.loads(TTWIN.read_text(encoding="utf-8")):
            tt[it["uid"]] = it
    gold = {}
    if TEMPLATES.is_file():
        gold = json.loads(TEMPLATES.read_text(encoding="utf-8")).get("classes") or {}
    gold_uid = {rec.get("uid"): k for k, rec in gold.items()}

    items = []
    for row in q["items"]:
        uid = row["uid"]
        tw = tt.get(uid) or {}
        a = tw.get("assessment") or {}
        key = row.get("key") or a.get("mcq_key")
        comm = a.get("examiner_comment") or {}
        folder = row["folder"]
        opts = row.get("options") or tw.get("options") or {}
        if isinstance(opts, dict):
            options = {k: opts[k] for k in ("A", "B", "C", "D") if opts.get(k)}
        else:
            options = {}
        b64 = _b64(folder)
        stem_raw = row.get("stem") or tw.get("stem") or ""
        stem = learner_stem(stem_raw, options, uid, has_figure=bool(b64))
        disp_opts = learner_options(options)
        lbs = (lbs_doc.get("items") or {}).get(uid)
        if lbs is not None:
            lbs["key"] = key
            lbs["examiner_comment"] = comm.get("text") if comm.get("present") else None
        items.append(
            {
                "uid": uid,
                "folder": folder,
                "spectrum_types": row.get("spectrum_types") or [],
                "item_type": row.get("item_type") or tw.get("item_type"),
                "visual_form": row.get("visual_form"),
                "is_spectrum_plot": bool(row.get("is_spectrum_plot")),
                "stem": stem,
                "stem_raw": stem_raw,
                "options": disp_opts,
                "options_raw": options,
                "options_are_figure": options_are_figure(options),
                "key": key,
                "examiner_comment": comm.get("text") if comm.get("present") else None,
                "has_original": bool(b64),
                "original_base64": b64,
                "original_url": f"/media/{folder}/original.png" if b64 else None,
                "aliphatic_class": gold_uid.get(uid),
                "complete_exam": bool(tw.get("complete_exam")),
                "has_lbs": bool(lbs),
            }
        )
    LBS_OUT.write_text(json.dumps(lbs_doc, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "spectra.practice.v2",
        "n": len(items),
        "n_mcq": sum(1 for it in items if it["options"] and it["key"]),
        "n_figure": sum(1 for it in items if it["original_base64"]),
        "n_examiner": sum(1 for it in items if it["examiner_comment"]),
        "n_lbs": sum(1 for it in items if it["has_lbs"]),
        "items": items,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        _export_examples()
        print("wrote", CURVES)
    except Exception as e:
        print("ir_examples skipped:", e)
    print(
        f"wrote {OUT} n={doc['n']} mcq={doc['n_mcq']} fig={doc['n_figure']} "
        f"examiner={doc['n_examiner']} lbs={doc['n_lbs']}"
    )
    print("wrote", LBS_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
