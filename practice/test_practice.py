#!/usr/bin/env python3
"""Self-test: MCQ-only pack, original stems keep tables, LBS schema, MS keys."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from display import learner_stem, paper_label, paper_short, presentation, technique  # noqa: E402
from extract_ms_keys import parse_ms_text, uid_to_ms_name  # noqa: E402
from lbs_schema import validate_item  # noqa: E402

PACK = HERE / "static" / "pack.json"
LBS = HERE / "static" / "lbs.json"
MS = HERE / "static" / "ms_keys.json"


def fail(msg: str) -> None:
    print("FAIL", msg)
    raise SystemExit(1)


def main() -> int:
    # display: keep the data-booklet table
    raw = (
        "The infrared spectrum of a compound is shown.\n\n"
        "bond | functional groups containing the bond | range\n"
        "C=O | carbonyl | 1670–1740\n\n"
        "Which functional group could the compound contain?\n"
        "A alcohol B acid C ester D nitrile"
    )
    opts = {"A": "alcohol", "B": "carboxylic acid", "C": "ester", "D": "nitrile"}
    stem = learner_stem(raw, opts, "9701_m24_qp_12:q40", True)
    if "1670–1740" not in stem:
        fail("learner_stem dropped the IR table")
    if "Which functional group" not in stem:
        fail("learner_stem dropped the question")
    if technique(["ir", "ms"]) != "mixed":
        fail("mixed technique")
    if technique(["nmr"]) != "nmr":
        fail("nmr technique")
    if paper_label("9701_m19_qp_12:q30") != "March 2019 paper 12, question 30":
        fail("paper_label " + paper_label("9701_m19_qp_12:q30"))
    if paper_short("9701_s18_qp_11:q30") != "June 2018 · Q30":
        fail("paper_short")

    text_q = presentation(
        visual_form="text_only",
        is_spectrum_plot=False,
        original_kind="source_crop",
        options={"A": "2", "B": "4", "C": "6", "D": "7"},
        has_png=True,
    )
    if text_q["show_figure"] or not text_q["show_stem"] or not text_q["show_option_text"] or text_q["letter_select"]:
        fail("text-complete question must not render the scan: " + str(text_q))
    fig_q = presentation(
        visual_form="spectrum_plot",
        is_spectrum_plot=True,
        original_kind="source_crop",
        options={"A": "propan-1-ol", "B": "acid", "C": "ester", "D": "ketone"},
        has_png=True,
    )
    if not fig_q["show_figure"] or fig_q["show_stem"] or fig_q["show_option_text"] or not fig_q["letter_select"]:
        fail("spectrum PNG already carries stem/options: " + str(fig_q))
    letters = presentation(
        visual_form="spectrum_plot",
        is_spectrum_plot=True,
        original_kind="source_crop",
        options={"A": "spectrum A", "B": "spectrum B", "C": "spectrum C", "D": "spectrum D"},
        has_png=True,
    )
    if not letters["letter_select"] or not letters["show_figure"]:
        fail("figure options need letter selectors")

    sample = parse_ms_text("      30       B                                                                1\n")
    if sample.get(30) != "B":
        fail("parse_ms_text")
    if uid_to_ms_name("9701_s18_qp_11:q30") != "9701_Jun-18_ms_11.pdf":
        fail("uid_to_ms_name")

    pack = json.loads(PACK.read_text(encoding="utf-8"))
    if pack.get("schema") != "spectra.practice.v3":
        fail("pack schema " + str(pack.get("schema")))
    if pack["n"] < 50:
        fail("expected ≥50 MCQs, got " + str(pack["n"]))
    for it in pack["items"]:
        if not it.get("key"):
            fail("unkeyed " + it["uid"])
        if it.get("item_type") not in {"mcq", "mcq_diagram", "mcq_table", "three_statement"}:
            fail("non-mcq " + it["uid"])
        opts = it.get("options") or {}
        if sum(1 for k in "ABCD" if k in (it.get("options_raw") or opts or {})) < 4:
            fail("options " + it["uid"])
        if it["item_type"] == "structured":
            fail("structured leaked")
    tech = pack.get("techniques") or {}
    if tech.get("ir", 0) < 20 or tech.get("ms", 0) < 10:
        fail("technique mix " + str(tech))
    # table kept on the known item
    m24 = next(x for x in pack["items"] if x["uid"] == "9701_m24_qp_12:q40")
    if "1040–1300" not in (m24.get("stem") or "") and "1040-1300" not in (m24.get("stem") or ""):
        fail("m24 stem lost the printed IR table")
    if not m24.get("show_figure") or not m24.get("original_base64"):
        fail("m24 missing original figure")
    if m24.get("show_stem") or not m24.get("letter_select"):
        fail("m24 figure already has the printed stem and A–D")
    m18 = next(x for x in pack["items"] if x["uid"] == "9701_m18_qp_12:q30")
    if m18.get("show_figure") or m18.get("original_base64"):
        fail("m18 is complete text — must not show the question scan")
    if not m18.get("show_stem") or not m18.get("show_option_text"):
        fail("m18 must show encoded stem and A–D text")
    if (m18.get("options") or {}).get("B") != "4":
        fail("m18 option B")

    lbs = json.loads(LBS.read_text(encoding="utf-8"))
    missing = []
    for it in pack["items"]:
        rec = (lbs.get("items") or {}).get(it["uid"])
        if not rec:
            missing.append(it["uid"])
            continue
        err = validate_item(it["uid"], rec, key=it["key"])
        if err:
            fail("lbs " + err[0])
    if missing:
        fail("lbs missing " + str(missing[:8]) + f" ({len(missing)})")

    ms = json.loads(MS.read_text(encoding="utf-8"))
    # existing TTwin keys must match the mark scheme where both exist
    n_check = 0
    for it in pack["items"]:
        paper, _, qn = it["uid"].partition(":q")
        letter = (ms.get("papers") or {}).get(paper, {}).get(qn)
        if letter:
            n_check += 1
            if letter != it["key"]:
                fail(f"key mismatch {it['uid']} pack={it['key']} ms={letter}")
    if n_check < 40:
        fail("too few MS cross-checks " + str(n_check))
    print(
        "PASS",
        f"n={pack['n']} lbs={lbs.get('n')} fig={pack.get('n_figure')} "
        f"tech={tech} ms_checked={n_check}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
