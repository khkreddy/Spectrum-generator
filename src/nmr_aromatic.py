"""Aromatic 13C/1H shifts from Astra increment tables (harvest-calibrated)."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from rdkit import Chem

RULES = Path(__file__).resolve().parents[1] / "data" / "rules" / "nmr_increments_astra.json"


def _load():
    if not RULES.is_file():
        return 128.5, 7.27, [], []
    d = json.loads(RULES.read_text(encoding="utf-8"))
    return (
        float(d.get("benzene_13C_base") or 128.5),
        float(d.get("benzene_1H_base") or 7.27),
        d.get("c13_increments") or [],
        d.get("h1_increments") or [],
    )


C_BASE, H_BASE, C_INC, H_INC = _load()
H_BY_GROUP = {r["group"]: r for r in H_INC}


def _positions(mol, ipso: int) -> dict[str, list[int]]:
    atom = mol.GetAtomWithIdx(ipso)
    ortho = [n.GetIdx() for n in atom.GetNeighbors() if n.GetIsAromatic() and n.GetSymbol() == "C"]
    meta = []
    for o in ortho:
        for n in mol.GetAtomWithIdx(o).GetNeighbors():
            if n.GetIsAromatic() and n.GetSymbol() == "C" and n.GetIdx() not in ortho and n.GetIdx() != ipso:
                meta.append(n.GetIdx())
    para = []
    for m in meta:
        for n in mol.GetAtomWithIdx(m).GetNeighbors():
            j = n.GetIdx()
            if n.GetIsAromatic() and n.GetSymbol() == "C" and j != ipso and j not in ortho and j not in meta:
                para.append(j)
    return {
        "ipso": [ipso],
        "ortho": list(dict.fromkeys(ortho)),
        "meta": list(dict.fromkeys(meta)),
        "para": list(dict.fromkeys(para)),
    }


def _apply_c(mol) -> dict[int, float]:
    shifts = {
        a.GetIdx(): C_BASE
        for a in mol.GetAtoms()
        if a.GetIsAromatic() and a.GetSymbol() == "C"
    }
    for rule in C_INC:
        q = Chem.MolFromSmarts(rule.get("smarts") or "")
        if q is None:
            continue
        for match in mol.GetSubstructMatches(q):
            ipso = match[0]
            if ipso not in shifts:
                continue
            pos = _positions(mol, ipso)
            for role, key in (("ipso", "ipso"), ("ortho", "ortho"), ("meta", "meta"), ("para", "para")):
                inc = float(rule.get(key) or 0)
                for idx in pos[role]:
                    if idx in shifts:
                        shifts[idx] += inc
    return shifts


def _apply_h(mol) -> dict[int, float]:
    """Map aromatic H atom index → ppm."""
    c_shifts_roles = []  # list of (ipso, rule group)
    for rule in C_INC:
        q = Chem.MolFromSmarts(rule.get("smarts") or "")
        if q is None:
            continue
        for match in mol.GetSubstructMatches(q):
            c_shifts_roles.append((match[0], rule["group"]))
    h_ppm = {}
    for atom in mol.GetAtoms():
        if atom.GetSymbol() != "H":
            continue
        neigh = atom.GetNeighbors()
        if not neigh:
            continue
        c = neigh[0]
        if not (c.GetIsAromatic() and c.GetSymbol() == "C"):
            continue
        ppm = H_BASE
        cid = c.GetIdx()
        for ipso, group in c_shifts_roles:
            inc = H_BY_GROUP.get(group)
            if not inc:
                continue
            pos = _positions(mol, ipso)
            if cid in pos["ipso"]:
                continue  # no H on ipso if substituted
            if cid in pos["ortho"]:
                ppm += float(inc.get("ortho") or 0)
            elif cid in pos["meta"]:
                ppm += float(inc.get("meta") or 0)
            elif cid in pos["para"]:
                ppm += float(inc.get("para") or 0)
        h_ppm[atom.GetIdx()] = ppm
    return h_ppm


def carbon_peaks(mol) -> list[dict]:
    sh = _apply_c(mol)
    # merge by rounded 0.5 ppm after grouping equivalent ranks
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))
    buckets = defaultdict(list)
    for idx, ppm in sh.items():
        buckets[ranks[idx]].append(ppm)
    peaks = []
    for r, vals in buckets.items():
        peaks.append({"delta": round(sum(vals) / len(vals), 1), "id": f"C{r}", "n": len(vals)})
    peaks.sort(key=lambda p: -p["delta"])
    return peaks


def proton_aromatic_ppm(mol) -> dict[int, float]:
    return _apply_h(mol)
