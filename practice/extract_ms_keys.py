#!/usr/bin/env python3
"""Read Cambridge 9701 Paper 1 mark-scheme PDFs into a uid → A–D map.

Does not rewrite freeze. Runtime LBS never opens a PDF.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/harik/awm_build")
MS_DIR = ROOT / "data/sources/aschem/Paper-1"
OUT = Path(__file__).resolve().parent / "static" / "ms_keys.json"

SEASON = {"m": "Mar", "s": "Jun", "w": "Nov"}
UID_RE = re.compile(r"^9701_([msw])(\d{2})_qp_(\d+):q(\d+)$")
# "      30       B                                                                1"
ROW_RE = re.compile(r"^\s*(\d{1,2})\s+([A-D])\s+1\s*$", re.M)
MONTH = {"Mar": "m", "Jun": "s", "Nov": "w"}
FILE_RE = re.compile(r"^9701_(Mar|Jun|Nov)-(\d{2})_ms_(\d+)\.pdf$")


def uid_to_ms_name(uid: str) -> str | None:
    m = UID_RE.match(uid)
    if not m:
        return None
    season, yy, paper, _q = m.groups()
    return f"9701_{SEASON[season]}-{yy}_ms_{paper}.pdf"


def parse_ms_text(text: str) -> dict[int, str]:
    keys: dict[int, str] = {}
    for n, letter in ROW_RE.findall(text or ""):
        qn = int(n)
        if 1 <= qn <= 40:
            keys[qn] = letter
    return keys


def pdftotext(path: Path) -> str:
    r = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return r.stdout


def load_all_ms(ms_dir: Path = MS_DIR) -> dict[str, dict[int, str]]:
    """filename → {qnum: letter}."""
    out: dict[str, dict[int, str]] = {}
    for p in sorted(ms_dir.glob("9701_*_ms_*.pdf")):
        try:
            keys = parse_ms_text(pdftotext(p))
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        if keys:
            out[p.name] = keys
    return out


def key_for_uid(uid: str, tables: dict[str, dict[int, str]]) -> str | None:
    name = uid_to_ms_name(uid)
    if not name:
        return None
    m = UID_RE.match(uid)
    qn = int(m.group(4))
    table = tables.get(name)
    if not table:
        return None
    return table.get(qn)


def main() -> int:
    tables = load_all_ms()
    n_q = sum(len(v) for v in tables.values())
    print(f"ms files parsed {len(tables)} questions {n_q}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # invert to uid-ready index: season/yy/paper → keys
    index = {}
    for name, keys in tables.items():
        fm = FILE_RE.match(name)
        if not fm:
            continue
        month, yy, paper = fm.groups()
        index[f"9701_{MONTH[month]}{yy}_qp_{paper}"] = {str(k): v for k, v in keys.items()}
    doc = {
        "schema": "spectra.ms_keys.v1",
        "source": str(MS_DIR),
        "n_papers": len(index),
        "n_keys": sum(len(v) for v in index.values()),
        "papers": index,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print("wrote", OUT, "papers", doc["n_papers"], "keys", doc["n_keys"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
