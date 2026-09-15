#!/usr/bin/env python3
"""SMILES → exam-quality IR/MS/1H/13C JSON + TikZ."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate import generate
from render_tikz import render_all


def write_molecule(smiles: str, name: str, dest: Path) -> dict:
    spec = generate(smiles, name=name)
    tikz = render_all(spec)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "spectrum.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    for k, code in tikz.items():
        (dest / f"{k}.tikz").write_text(code + "\n", encoding="utf-8")
    (dest / "identifiable.json").write_text(json.dumps(spec["identifiable"], indent=2) + "\n", encoding="utf-8")
    return spec


def main(argv: list[str]) -> int:
    mols = json.loads((ROOT / "data" / "molecules.json").read_text(encoding="utf-8"))
    if argv[1:] == ["canary"]:
        for m in mols["canary"]:
            dest = ROOT / "out" / "canary" / m["id"]
            spec = write_molecule(m["smiles"], m["name"], dest)
            print(m["id"], spec["formula"], spec["identifiable"])
        return 0
    if argv[1:] == ["exam"]:
        for m in mols["exam_9701"]:
            dest = ROOT / "out" / "match_9701" / m["id"]
            write_molecule(m["smiles"], m["id"], dest)
            print("wrote", m["id"])
        return 0
    if len(argv) >= 3:
        smiles, name = argv[1], argv[2]
        dest = ROOT / "out" / "one" / name
        write_molecule(smiles, name, dest)
        print(dest)
        return 0
    print("usage: cli.py canary | exam | <smiles> <name>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
