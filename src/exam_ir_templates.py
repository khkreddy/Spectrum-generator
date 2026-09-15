"""Exam-paper IR TikZ → aliphatic class templates.

Warped 9701 axis (4000–2000 left 40%, 2000–500 stretched) is inverted back
to wavenumber so the generator can interpolate T(ν). Aromatics and rings
are never used as class gold.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]
EXAM = ROOT / "out" / "exam_luna"
RULES = ROOT / "data" / "rules" / "exam_ir_templates.json"

TWO_SCALE = np.array(
    [
        [0.00, 4000.0],
        [0.20, 3000.0],
        [0.40, 2000.0],
        [0.60, 1500.0],
        [0.80, 1000.0],
        [1.00, 500.0],
    ]
)

# Single-panel aliphatic exam gold. Key molecule is acyclic non-aromatic.
CLASS_GOLD = {
    "ketone": ("9701_m23_qp_12_q38", 0, "CC(=O)C", "propanone"),
    "ester": ("9701_m24_qp_12_q40", 0, "CCOC(=O)C", "ethyl ethanoate / ester C=O+C-O"),
    "primary_alcohol": ("9701_s18_qp_11_q30", 0, "CCCO", "propan-1-ol"),
    "secondary_alcohol": ("9701_w19_qp_11_q30", 0, "CC(C)O", "propan-2-ol"),
    "acetic": ("9701_s20_qp_11_q29", 0, "CC(=O)O", "ethanoic acid"),
    "acid": ("9701_s20_qp_13_q25", 0, "CCC(=O)O", "propanoic acid"),
    "polyol": ("9701_w18_qp_12_q30", 0, "OCC(O)CO", "glycerol"),
    "ethanol": ("9701_s18_qp_11_q30", 0, "CCO", "propan-1-ol used as 1° alcohol prior for ethanol"),
}


def xf_to_wn(xf: np.ndarray, ticks: np.ndarray | None = None) -> np.ndarray:
    t = ticks if ticks is not None and len(ticks) >= 2 else TWO_SCALE
    order = np.argsort(t[:, 0])
    return np.interp(xf, t[order, 0], t[order, 1])


def wn_to_xf(wn: float) -> float:
    if wn >= 2000:
        return (4000.0 - wn) / 2000.0 * 0.40
    return 0.40 + (2000.0 - wn) / 1500.0 * 0.60


def parse_exam_ir(tikz: str) -> list[np.ndarray]:
    """Each panel → Nx2 array (wn, T), 4000→500."""
    tick_lists = re.findall(r"foreach \\x/\\t in \{([^}]+)\}", tikz)
    blobs = re.findall(r"coordinates\s*\{([^}]+)\}", tikz, flags=re.S)
    out = []
    for i, blob in enumerate(blobs):
        pts = [
            (float(a), float(b))
            for a, b in re.findall(r"\(([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)\)", blob)
        ]
        if len(pts) < 20:
            continue
        xs = np.array([p[0] for p in pts], float)
        ts = np.array([p[1] for p in pts], float)
        ticks = TWO_SCALE
        if i < len(tick_lists):
            parsed = [
                (float(a), float(b))
                for a, b in re.findall(r"([-+]?\d*\.?\d+)/(\d+)", tick_lists[i])
            ]
            if len(parsed) >= 4:
                ticks = np.array(parsed, float)
                # tick x may be cm 0–10
                if ticks[:, 0].max() > 1.5:
                    ticks[:, 0] = ticks[:, 0] / ticks[:, 0].max()
        if xs.max() <= 12.5:
            xf = xs / max(xs.max(), 10.0) if xs.max() > 1.5 else xs
            wn = xf_to_wn(xf, ticks)
        else:
            wn = xs
        m = (wn >= 450) & (wn <= 4050) & (ts >= 0) & (ts <= 105)
        arr = np.column_stack([wn[m], ts[m]])
        if len(arr) < 20:
            continue
        order = np.argsort(arr[:, 0])
        out.append(arr[order])
    return out


def troughs(arr: np.ndarray, t_cut: float = 88.0) -> list[dict]:
    """Local minima with FWHM → sharp / rounded / broad."""
    if len(arr) < 8:
        return []
    wn, t = arr[:, 0], arr[:, 1]
    found = []
    for i in range(2, len(arr) - 2):
        if not (t[i] <= t[i - 1] and t[i] <= t[i + 1] and t[i] < t_cut):
            continue
        if t[i] > t[i - 2] or t[i] > t[i + 2]:
            continue
        if float(wn[i]) > 3650 and t[i] > 40:
            continue
        if t[i] > 70:
            continue
        depth = float(max(0.0, 92.0 - t[i]))
        half = t[i] + 0.5 * (min(92.0, t[max(0, i - 8) : i + 9].max()) - t[i])
        lo = i
        while lo > 0 and t[lo] <= half:
            lo -= 1
        hi = i
        while hi < len(t) - 1 and t[hi] <= half:
            hi += 1
        fwhm = abs(float(wn[hi] - wn[lo]))
        if fwhm < 70:
            shape = "sharp"
        elif fwhm < 280:
            shape = "rounded"
        else:
            shape = "broad"
        found.append(
            {
                "wn": round(float(wn[i]), 0),
                "Tmin": round(float(t[i]), 1),
                "depth": round(depth, 1),
                "fwhm": round(fwhm, 0),
                "shape": shape,
            }
        )
    # keep deepest in 40 cm-1 clusters
    found.sort(key=lambda p: p["Tmin"])
    kept = []
    for p in found:
        if any(abs(p["wn"] - q["wn"]) < 40 for q in kept):
            continue
        kept.append(p)
    kept.sort(key=lambda p: -p["wn"])
    return kept[:12]


def is_aliphatic_acyclic(smiles: str) -> bool:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    if any(a.GetIsAromatic() for a in mol.GetAtoms()):
        return False
    if mol.GetRingInfo().NumRings() > 0:
        return False
    return True


def resample(arr: np.ndarray, grid: np.ndarray | None = None) -> np.ndarray:
    grid = grid if grid is not None else np.arange(4000, 499, -5)
    t = np.interp(grid, arr[:, 0], arr[:, 1], left=arr[0, 1], right=arr[-1, 1])
    return np.column_stack([grid, t])


def build() -> dict:
    classes = {}
    for key, (folder, panel, smiles, name) in CLASS_GOLD.items():
        p = EXAM / folder / "figure.tikz"
        if not p.is_file():
            continue
        panels = parse_exam_ir(p.read_text(encoding="utf-8"))
        if not panels or panel >= len(panels):
            continue
        arr = panels[panel]
        rs = resample(arr)
        classes[key] = {
            "uid": folder,
            "folder": folder,
            "smiles": smiles,
            "name": name,
            "aliphatic_acyclic": is_aliphatic_acyclic(smiles),
            "troughs": troughs(arr),
            "curve": [[round(float(a), 1), round(float(b), 1)] for a, b in rs],
        }
    # human folder → uid
    for key, rec in classes.items():
        folder = rec["folder"]
        a, b = folder.rsplit("_q", 1)
        rec["uid"] = f"{a}:q{b}"
    RULES.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "exam_ir_templates.v1",
        "axis": "9701 two-scale 4000–2000 / 2000–500",
        "scope": "aliphatic acyclic",
        "n": len(classes),
        "classes": classes,
    }
    RULES.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


_CACHE: dict[str, np.ndarray] | None = None


def templates() -> dict[str, np.ndarray]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not RULES.is_file():
        build()
    doc = json.loads(RULES.read_text(encoding="utf-8"))
    out = {}
    for key, rec in (doc.get("classes") or {}).items():
        cur = rec.get("curve") or []
        if len(cur) >= 16:
            arr = np.array(cur, float)
            order = np.argsort(arr[:, 0])
            out[key] = arr[order]
    _CACHE = out
    return out


def T_exam(nu: float, key: str) -> float | None:
    arr = templates().get(key)
    if arr is None or arr.size == 0:
        return None
    return float(np.interp(nu, arr[:, 0], arr[:, 1], left=arr[0, 1], right=arr[-1, 1]))


if __name__ == "__main__":
    doc = build()
    print("wrote", RULES, "n", doc["n"])
    for k, rec in doc["classes"].items():
        tops = rec["troughs"][:5]
        print(k, rec["name"], "troughs", [(t["wn"], t["Tmin"], t["shape"]) for t in tops])
