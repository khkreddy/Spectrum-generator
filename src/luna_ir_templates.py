"""Luna vision TikZ of experimental IR → class templates for the aliphatic generator."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

ENC = Path(__file__).resolve().parents[1] / "out" / "luna_encodings"

# Acyclic non-aromatic only. Aromatics/rings excluded.
FILES = {
    "ethanol": "08-ethanol/ir.tikz",
    "primary_alcohol": "22-1-propanol/ir.tikz",  # 1-alkanol prototype
    "secondary_alcohol": "23-2-propanol/ir.tikz",
    "acid": "317-propionic-acid/ir.tikz",
    "acetic": "10-acetic-acid/ir.tikz",
    "ketone": "423-acetone/ir.tikz",
    "aldehyde": "78-propionaldehyde/ir.tikz",
    "ester": "11-ethyl-acetate/ir.tikz",
    "alkyl_bromide": "07-1-bromobutane/ir.tikz",
    "polyol": "43-glycerol/ir.tikz",
}


def _parse_tikz(path: Path) -> np.ndarray:
    """Only vertices inside plot coordinates {...}. Never the axis rectangle."""
    text = path.read_text(encoding="utf-8")
    blobs = re.findall(r"coordinates\s*\{([^}]+)\}", text, flags=re.S)
    if not blobs:
        blobs = [text]
    pts = []
    for blob in blobs:
        pts.extend(
            (float(a), float(b))
            for a, b in re.findall(r"\(([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)\)", blob)
        )
    if len(pts) < 16:
        return np.zeros((0, 2))
    arr = np.array(pts, float)
    m = (arr[:, 0] >= 380) & (arr[:, 0] <= 4100) & (arr[:, 1] >= 0) & (arr[:, 1] <= 105)
    arr = arr[m]
    drop = (np.isclose(arr[:, 0], 4000) | np.isclose(arr[:, 0], 400)) & (
        np.isclose(arr[:, 1], 0) | np.isclose(arr[:, 1], 100)
    )
    arr = arr[~drop]
    if arr.size == 0:
        return np.zeros((0, 2))
    order = np.argsort(arr[:, 0])
    return arr[order]


def load_all() -> dict[str, np.ndarray]:
    out = {}
    for key, rel in FILES.items():
        p = ENC / rel
        if p.is_file():
            a = _parse_tikz(p)
            if a.size:
                out[key] = a
    return out


_CACHE: dict[str, np.ndarray] | None = None


def templates() -> dict[str, np.ndarray]:
    global _CACHE
    if _CACHE is None:
        _CACHE = load_all()
    return _CACHE


def T_template(nu: float, key: str) -> float | None:
    try:
        from exam_ir_templates import T_exam

        tv = T_exam(nu, key)
        if tv is not None:
            return tv
    except Exception:
        pass
    arr = templates().get(key)
    if arr is None or arr.size == 0:
        return None
    return float(np.interp(nu, arr[:, 0], arr[:, 1], left=arr[0, 1], right=arr[-1, 1]))


def alcohol_template_key(feat: dict) -> str:
    f = feat.get("flags") or {}
    nC = int(feat.get("n_C") or 2)
    n_oh = 0
    if f.get("primary_alcohol"):
        n_oh += 1
    if f.get("secondary_alcohol"):
        n_oh += 1
    # glycerol: 3 OH
    if nC >= 3 and f.get("secondary_alcohol") and f.get("primary_alcohol"):
        if "polyol" in templates():
            return "polyol"
    if f.get("secondary_alcohol") and not f.get("primary_alcohol"):
        return "secondary_alcohol"
    if nC <= 2:
        return "ethanol"
    return "primary_alcohol"


def acid_template_key(feat: dict) -> str:
    f = feat.get("flags") or {}
    if f.get("alpha_CH3_acid") and int(feat.get("n_C") or 0) == 2:
        return "acetic"
    return "acid"
