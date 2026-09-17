#!/usr/bin/env python3
"""Pack 9701 spectroscopy MCQs: original stems, original figures, LBS keys.

Only items with A–D options and a mark-scheme (or TTwin) key.
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from display import (  # noqa: E402
    learner_options,
    learner_stem,
    options_are_figure,
    presentation,
    technique,
)
from lbs_followups import build as build_lbs  # noqa: E402
from lbs_schema import LETTERS, validate_item  # noqa: E402

CANON = Path(__file__).resolve().parents[1]
HARVEST = Path("/home/harik/awm_build/data/spectra")
QUEST = CANON / "review" / "static" / "questions.json"
TTWIN = Path("/home/harik/TTwin/data/questions/chemistry-senior.json")
OUT = CANON / "practice" / "static" / "pack.json"
TEMPLATES = CANON / "data" / "rules" / "exam_ir_templates.json"
LBS_OUT = CANON / "practice" / "static" / "lbs.json"
CURVES = CANON / "practice" / "static" / "ir_examples.json"
MS_KEYS = CANON / "practice" / "static" / "ms_keys.json"
MEDIA = CANON / "practice" / "static" / "media"

MCQ_TYPES = {"mcq", "mcq_diagram", "mcq_table", "three_statement"}
UID_RE = re.compile(r"^(9701_[msw]\d{2}_qp_\d+):q(\d+)$")


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


def _ms_key(uid: str, ms: dict) -> str | None:
    m = UID_RE.match(uid)
    if not m:
        return None
    return (ms.get("papers") or {}).get(m.group(1), {}).get(m.group(2))


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


def _copy_media(folder: str) -> str | None:
    src = HARVEST / "items" / folder / "original.png"
    if not src.is_file():
        return None
    dest = MEDIA / folder / "original.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return f"media/{folder}/original.png"


def main() -> int:
    lbs_doc = build_lbs()
    q = json.loads(QUEST.read_text(encoding="utf-8"))
    ms = json.loads(MS_KEYS.read_text(encoding="utf-8")) if MS_KEYS.is_file() else {"papers": {}}
    tt = {}
    if TTWIN.is_file():
        for it in json.loads(TTWIN.read_text(encoding="utf-8")):
            tt[it["uid"]] = it
    gold = {}
    if TEMPLATES.is_file():
        gold = json.loads(TEMPLATES.read_text(encoding="utf-8")).get("classes") or {}
    gold_uid = {rec.get("uid"): k for k, rec in gold.items()}
    index_rows = {}
    idx_path = HARVEST / "INDEX.json"
    if idx_path.is_file():
        for rec in json.loads(idx_path.read_text(encoding="utf-8")):
            if rec.get("item_uid"):
                index_rows[rec["item_uid"]] = rec

    items = []
    skipped = {"not_mcq": 0, "no_options": 0, "no_key": 0}
    for row in q["items"]:
        uid = row["uid"]
        item_type = row.get("item_type") or ""
        if item_type not in MCQ_TYPES:
            skipped["not_mcq"] += 1
            continue
        tw = tt.get(uid) or {}
        a = tw.get("assessment") or {}
        key = row.get("key") or a.get("mcq_key") or _ms_key(uid, ms)
        comm = a.get("examiner_comment") or {}
        folder = row["folder"]
        opts = row.get("options") or tw.get("options") or {}
        if isinstance(opts, dict):
            options = {k: opts[k] for k in LETTERS if k in opts}
        else:
            options = {}
        if sum(1 for k in LETTERS if k in options) < 4:
            skipped["no_options"] += 1
            continue
        if not key:
            skipped["no_key"] += 1
            continue
        meta = index_rows.get(uid) or {}
        png_exists = (HARVEST / "items" / folder / "original.png").is_file() or (
            HARVEST / "items" / folder / "original.base64"
        ).is_file()
        pres = presentation(
            visual_form=row.get("visual_form") or meta.get("visual_form"),
            is_spectrum_plot=bool(row.get("is_spectrum_plot") or meta.get("is_spectrum_plot")),
            original_kind=meta.get("original_kind"),
            options=options,
            has_png=png_exists,
        )
        b64 = _b64(folder) if pres["show_figure"] else None
        media = _copy_media(folder) if pres["show_figure"] else None
        stem_raw = row.get("stem") or tw.get("stem") or ""
        stem = learner_stem(stem_raw, options, uid, has_figure=pres["show_figure"])
        disp_opts = learner_options(options)
        if not pres["show_option_text"]:
            disp_opts = {k: "" for k in LETTERS}
        lbs = (lbs_doc.get("items") or {}).get(uid)
        if lbs is not None:
            lbs["key"] = key
            lbs["examiner_comment"] = comm.get("text") if comm.get("present") else None
            bad = validate_item(uid, lbs, key=key)
            if bad:
                print("LBS schema", uid, bad[:3])
        types = row.get("spectrum_types") or []
        items.append(
            {
                "uid": uid,
                "folder": folder,
                "spectrum_types": types,
                "technique": technique(types),
                "item_type": item_type,
                "visual_form": row.get("visual_form"),
                "is_spectrum_plot": bool(row.get("is_spectrum_plot")),
                "original_kind": meta.get("original_kind"),
                "stem": stem,
                "stem_raw": stem_raw,
                "options": disp_opts,
                "options_raw": options,
                "options_are_figure": options_are_figure(options),
                "show_figure": pres["show_figure"],
                "show_stem": pres["show_stem"],
                "show_option_text": pres["show_option_text"],
                "letter_select": pres["letter_select"],
                "prompt_in_figure": pres["prompt_in_figure"],
                "key": key,
                "key_source": "ttwin" if a.get("mcq_key") else "mark_scheme",
                "examiner_comment": comm.get("text") if comm.get("present") else None,
                "has_original": bool(b64),
                "original_base64": b64,
                "original_url": media,
                "aliphatic_class": gold_uid.get(uid),
                "complete_exam": bool(tw.get("complete_exam")),
                "has_lbs": bool(lbs),
            }
        )

    LBS_OUT.write_text(json.dumps(lbs_doc, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tech = {}
    for it in items:
        tech[it["technique"]] = tech.get(it["technique"], 0) + 1
    doc = {
        "schema": "spectra.practice.v3",
        "n": len(items),
        "n_mcq": len(items),
        "n_figure": sum(1 for it in items if it["original_base64"]),
        "n_examiner": sum(1 for it in items if it["examiner_comment"]),
        "n_lbs": sum(1 for it in items if it["has_lbs"]),
        "techniques": tech,
        "skipped": skipped,
        "items": items,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        _export_examples()
        print("wrote", CURVES)
    except Exception as e:
        print("ir_examples skipped:", e)
    print(
        f"wrote {OUT} n={doc['n']} fig={doc['n_figure']} "
        f"examiner={doc['n_examiner']} lbs={doc['n_lbs']} tech={tech} skipped={skipped}"
    )
    print("wrote", LBS_OUT, "n", lbs_doc.get("n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
