#!/usr/bin/env python3
"""Peak positions, shapes and ranges from aliphatic acyclic experimental IR.

Sources, in order of trust:
  1. Luna TikZ encodings of SDBS liquid-film GIFs (trough + FWHM + shape).
  2. Digitised GIF curve_ds in experimental_peaks.jsonl (same trough finder).
GIF peak-table minima are not used: they routinely mark the 3850 cm⁻¹ y-axis
as an O–H trough.

Aromatics and rings are out of scope. Axis junk (ν > 3650, 1850–2400 unless
the family is alkyne/nitrile) is dropped.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from rdkit import RDLogger

from exam_ir_templates import T_exam, troughs
from features import features as mol_features
from luna_ir_templates import ENC, FILES, _parse_tikz
from names import CATALOG, resolve

RDLogger.DisableLog("rdApp.*")

OH_FAMILIES = {
    "primary_alcohol",
    "secondary_alcohol",
    "tertiary_alcohol",
    "ethanol",
    "methanol",
    "polyol",
    "acid",
    "acetic",
}
ALLOWED_OVERLAY = {
    "primary_alcohol": {"CH2_scissor", "CH3_bend", "C-O_primary"},
    "secondary_alcohol": {"C-O_secondary", "CH3_bend"},
    "ethanol": {"CH2_scissor", "C-O_primary"},
    "ketone": {"CH3_bend"},
    "ester": {"C-O_ester_2", "CH3_bend"},
}

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data" / "inventory.jsonl"
PEAKS = ROOT / "data" / "experimental_peaks.jsonl"
OUT = ROOT / "data" / "rules" / "aliphatic_experimental_peaks.json"

LUNA_FOLDER = {
    "08-ethanol": "ethanol",
    "22-1-propanol": "primary_alcohol",
    "23-2-propanol": "secondary_alcohol",
    "10-acetic-acid": "acetic",
    "317-propionic-acid": "acid",
    "423-acetone": "ketone",
    "78-propionaldehyde": "aldehyde",
    "11-ethyl-acetate": "ester",
    "07-1-bromobutane": "alkyl_bromide",
    "43-glycerol": "polyol",
    "21-methanol": "methanol",
}

EXCLUDE_CAT = {
    "Arenes",
    "Haloarenes",
    "Phenols",
    "Heterocycles",
    "Cycloalkanes",
    "Nitro compounds",
    "Biomolecules",
}
KEEP_CAT = {
    "Alkanes",
    "Alkenes",
    "Alkynes",
    "Alcohols",
    "Carboxylic acids",
    "Esters",
    "Aldehydes",
    "Ketones",
    "Alkyl halides",
    "Ethers",
    "Nitriles",
    "Acid chlorides",
    "Anhydrides",
    "Amines",
    "Amides",
}
RINGY = re.compile(
    r"cyclo|aromatic|aryl|phenyl|benzene|phenol|furan|pyridine|aniline|"
    r"nitrobenzene|toluene|naphthal|benzo|benzyl|styrene",
    re.I,
)

FAMILY_FROM_SUB = [
    (re.compile(r"1° alcohol|primary alcohol", re.I), "primary_alcohol"),
    (re.compile(r"2° alcohol|secondary alcohol", re.I), "secondary_alcohol"),
    (re.compile(r"3° alcohol|tertiary alcohol", re.I), "tertiary_alcohol"),
    (re.compile(r"aliphatic acid|alkanoic", re.I), "acid"),
    (re.compile(r"aliphatic ketone", re.I), "ketone"),
    (re.compile(r"aliphatic aldehyde", re.I), "aldehyde"),
    (re.compile(r"acetate|aliphatic ester|ester", re.I), "ester"),
    (re.compile(r"bromide|chloride|iodide|1° halide|alkyl halide", re.I), "alkyl_halide"),
    (re.compile(r"terminal alkyne|internal alkyne", re.I), "alkyne"),
    (re.compile(r"terminal alkene|internal alkene", re.I), "alkene"),
    (re.compile(r"straight chain|branched", re.I), "alkane"),
    (re.compile(r"aliphatic nitrile|nitrile", re.I), "nitrile"),
    (re.compile(r"dialkyl ether|ether", re.I), "ether"),
    (re.compile(r"acid chloride", re.I), "acid_chloride"),
    (re.compile(r"1° aliphatic amine", re.I), "amine"),
    (re.compile(r"primary amide|aliphatic amide", re.I), "amide"),
    (re.compile(r"polyol|diol|triol", re.I), "polyol"),
]


def _family_of_entry(rec: dict, feat: dict | None) -> str:
    folder = rec.get("folder") or ""
    if folder in LUNA_FOLDER:
        key = LUNA_FOLDER[folder]
        return "alkyl_halide" if key == "alkyl_bromide" else key
    if feat:
        f = feat.get("flags") or {}
        if f.get("carboxylic_acid"):
            return "acetic" if feat.get("n_C") == 2 else "acid"
        if f.get("ester"):
            return "ester"
        if "aldehyde" in (feat.get("carbonyls") or []):
            return "aldehyde"
        if "ketone" in (feat.get("carbonyls") or []):
            return "ketone"
        if f.get("secondary_alcohol") and f.get("primary_alcohol"):
            return "polyol"
        if f.get("secondary_alcohol") and not f.get("primary_alcohol"):
            return "secondary_alcohol"
        if f.get("tertiary_alcohol"):
            return "tertiary_alcohol"
        if f.get("alcohol_OH"):
            return "ethanol" if feat.get("n_C") <= 2 else "primary_alcohol"
        if f.get("alkyne") or f.get("alkyne_terminal"):
            return "alkyne"
        if f.get("alkene"):
            return "alkene"
        if f.get("nitrile"):
            return "nitrile"
        if f.get("CBr") or f.get("CCl"):
            return "alkyl_halide"
        if f.get("ether"):
            return "ether"
    blob = " ".join(
        str(rec.get(k) or "") for k in ("category", "subclass", "name", "compound_label")
    )
    for rx, fam in FAMILY_FROM_SUB:
        if rx.search(blob):
            return fam
    cat = rec.get("category") or ""
    return {
        "Alcohols": "primary_alcohol",
        "Carboxylic acids": "acid",
        "Ketones": "ketone",
        "Aldehydes": "aldehyde",
        "Esters": "ester",
        "Alkyl halides": "alkyl_halide",
        "Alkanes": "alkane",
        "Alkenes": "alkene",
        "Alkynes": "alkyne",
        "Nitriles": "nitrile",
        "Ethers": "ether",
        "Acid chlorides": "acid_chloride",
    }.get(cat, "other")


def _assign(wn: float, family: str) -> str:
    if family in {"acid", "acetic"}:
        if 2500 <= wn <= 3300:
            return "O-H_acid"
        if 1680 <= wn <= 1760:
            return "C=O"
        if 1200 <= wn <= 1320:
            return "C-O_acid"
        if 900 <= wn <= 960:
            return "O-H_dimer_oop"
        if 1400 <= wn <= 1480:
            return "CH2_scissor"
        if 1355 <= wn <= 1395:
            return "CH3_bend"
        if 2800 <= wn <= 3000:
            return "C-H"
    if family in {"primary_alcohol", "ethanol", "methanol", "secondary_alcohol", "tertiary_alcohol", "polyol"}:
        if 3180 <= wn <= 3550:
            return "O-H_alcohol"
        if 2800 <= wn <= 3000:
            return "C-H"
        if 1435 <= wn <= 1485:
            return "CH2_scissor"
        if 1355 <= wn <= 1395:
            return "CH3_bend"
        if family == "secondary_alcohol" and 1085 <= wn <= 1160:
            return "C-O_secondary"
        if family == "tertiary_alcohol" and 1120 <= wn <= 1210:
            return "C-O_tertiary"
        if 1000 <= wn <= 1085:
            return "C-O_primary"
        if 1086 <= wn <= 1160:
            return "C-O_secondary"
    if family in {"ketone", "aldehyde", "ester", "acid_chloride", "amide"}:
        if 1680 <= wn <= 1820:
            return "C=O"
        if family == "aldehyde" and 2680 <= wn <= 2860:
            return "C-H_aldehyde"
        if family == "ester" and 1180 <= wn <= 1280:
            return "C-O_ester"
        if family == "ester" and 1000 <= wn <= 1100:
            return "C-O_ester_2"
        if 1435 <= wn <= 1485:
            return "CH2_scissor"
        if 1355 <= wn <= 1395:
            return "CH3_bend"
        if 2800 <= wn <= 3000:
            return "C-H"
    if family == "alkyne" and 2080 <= wn <= 2260:
        return "C≡C"
    if family == "nitrile" and 2200 <= wn <= 2270:
        return "C≡N"
    if family == "alkene" and 1600 <= wn <= 1680:
        return "C=C"
    if family == "alkyl_halide" and 500 <= wn <= 750:
        return "C-X"
    if 1435 <= wn <= 1485:
        return "CH2_scissor"
    if 1355 <= wn <= 1395:
        return "CH3_bend"
    if 2800 <= wn <= 3000:
        return "C-H"
    if 3180 <= wn <= 3550:
        return "O-H"
    return "fingerprint"


def _keep_peak(wn: float, family: str) -> bool:
    if wn > 3650:
        return False
    if 1850 <= wn <= 2400 and family not in {"alkyne", "nitrile", "acid_chloride"}:
        return False
    if 3100 <= wn <= 3650 and family not in OH_FAMILIES:
        return False
    return 420 <= wn <= 3650


def _troughs_from_curve(ds: list) -> list[dict]:
    if not ds or len(ds) < 12:
        return []
    arr = np.array(ds, float)
    order = np.argsort(arr[:, 0])
    arr = arr[order]
    return troughs(arr, t_cut=88.0)


def _is_aliphatic(rec: dict) -> tuple[bool, dict | None]:
    cat = rec.get("category") or ""
    sub = rec.get("subclass") or ""
    name = rec.get("name") or rec.get("compound_label") or ""
    folder = rec.get("folder") or ""
    blob = f"{cat} {sub} {name} {folder}"
    if cat in EXCLUDE_CAT:
        return False, None
    if RINGY.search(blob):
        return False, None
    feat = None
    for cand in (name, rec.get("compound_label"), folder.split("-", 1)[-1].replace("-", " ")):
        if not cand:
            continue
        key = str(cand).strip().lower()
        looks_smi = bool(re.match(r"^[A-IK-Za-z0-9@+\-\[\]()=#$./\\]+$", str(cand))) and any(
            ch.isupper() for ch in str(cand)
        )
        if key not in CATALOG and key.replace(" ", "").replace("-", "") not in CATALOG and not looks_smi:
            continue
        try:
            smi = resolve(str(cand))["smiles"]
            feat = mol_features(smi)
            break
        except Exception:
            continue
    if feat is not None:
        return bool(feat.get("aliphatic_acyclic")), feat
    if cat in KEEP_CAT:
        return True, None
    if folder in LUNA_FOLDER:
        return True, None
    return False, None


def _consensus(rows: list[dict]) -> list[dict]:
    by = defaultdict(list)
    for r in rows:
        for p in r.get("peaks") or []:
            lab = p.get("assignment") or "fingerprint"
            if lab == "fingerprint":
                continue
            by[lab].append(p)
    out = []
    for lab, ps in sorted(by.items()):
        wns = [p["wn"] for p in ps]
        tmins = [p["Tmin"] for p in ps]
        fwhms = [p["fwhm"] for p in ps if p.get("fwhm")]
        shapes = [p["shape"] for p in ps if p.get("shape")]
        shape = max(set(shapes), key=shapes.count) if shapes else "rounded"
        med_wn = float(np.median(wns))
        out.append(
            {
                "assignment": lab,
                "wn": round(med_wn, 0),
                "wn_range": [round(min(wns), 0), round(max(wns), 0)],
                "Tmin_median": round(float(np.median(tmins)), 1),
                "Tmin_range": [round(min(tmins), 1), round(max(tmins), 1)],
                "fwhm_median": round(float(np.median(fwhms)), 0) if fwhms else None,
                "shape": shape,
                "n": len(ps),
            }
        )
    return out


# Exam-class keys that T_at interpolates. Overlay a band when the exam
# envelope sits near baseline at a diagnostic experimental trough.
EXAM_KEYS = {
    "primary_alcohol",
    "secondary_alcohol",
    "ethanol",
    "acid",
    "acetic",
    "ketone",
    "ester",
    "aldehyde",
    "polyol",
    "alkyl_bromide",
}


def _overlay_for(family: str, consensus: list[dict], prototype: dict | None) -> list[dict]:
    exam_key = {
        "alkyl_halide": "alkyl_bromide",
        "alkyl_bromide": "alkyl_bromide",
    }.get(family, family)
    bands = []
    proto_peaks = {p["assignment"]: p for p in (prototype or {}).get("peaks") or []}
    for c in consensus:
        lab = c["assignment"]
        proto = proto_peaks.get(lab)
        wn = float(proto["wn"] if proto else c["wn"])
        tmin = float(proto["Tmin"] if proto else c["Tmin_median"])
        fwhm = float((proto or {}).get("fwhm") or c.get("fwhm_median") or 80)
        shape = (proto or {}).get("shape") or c["shape"]
        exam_t = None
        if exam_key in EXAM_KEYS:
            try:
                exam_t = T_exam(wn, exam_key)
            except Exception:
                exam_t = None
        allowed = ALLOWED_OVERLAY.get(family)
        if allowed is not None and lab not in allowed:
            continue
        if allowed is None:
            continue
        missing = exam_t is None or exam_t > 70.0
        # Always restore the 1-alkanol CH2 scissor: exam gold of
        # 9701_s18_qp_11:q30 sits at T(1450)=83 (baseline).
        if family in {"primary_alcohol", "ethanol"} and lab == "CH2_scissor":
            missing = True
        if family == "secondary_alcohol" and lab == "C-O_secondary":
            missing = exam_t is None or exam_t > 70.0
        if family == "primary_alcohol" and lab == "CH3_bend":
            missing = exam_t is None or exam_t > 70.0
        if family == "primary_alcohol" and lab == "C-O_primary":
            missing = exam_t is None or exam_t > 60.0
        if not missing:
            continue
        if lab == "fingerprint":
            continue
        # Keep exam grain: do not punch deeper than the experimental median.
        bands.append(
            {
                "id": lab,
                "wn": round(wn, 0),
                "wn_range": c["wn_range"],
                "Tmin": round(max(8.0, tmin), 1),
                "fwhm": round(max(24.0, min(220.0, fwhm)), 0),
                "shape": shape,
                "source_family": family,
                "exam_T_before": None if exam_t is None else round(float(exam_t), 1),
            }
        )
    return bands


def build() -> dict:
    inv = [json.loads(l) for l in INV.read_text(encoding="utf-8").splitlines() if l.strip()]
    gif = {}
    if PEAKS.is_file():
        for line in PEAKS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            gif[rec["folder"]] = rec

    molecules = []
    skipped = {"ring_or_aromatic": 0, "no_ir": 0, "not_aliphatic_cat": 0}

    for rec in inv:
        ok, feat = _is_aliphatic(rec)
        if not ok:
            skipped["ring_or_aromatic"] += 1
            continue
        folder = rec["folder"]
        family = _family_of_entry(rec, feat)
        peaks = []
        source = None
        luna_key = LUNA_FOLDER.get(folder)
        if luna_key and luna_key in FILES:
            arr = _parse_tikz(ENC / FILES[luna_key])
            if arr.size:
                peaks = troughs(arr)
                source = f"luna:{folder}"
        if not peaks:
            g = gif.get(folder) or {}
            ir = g.get("ir") or {}
            if not ir.get("ok"):
                skipped["no_ir"] += 1
                continue
            peaks = _troughs_from_curve(ir.get("curve_ds") or [])
            source = f"gif_curve:{folder}"
        clean = []
        for p in peaks:
            wn = float(p["wn"])
            if not _keep_peak(wn, family):
                continue
            q = dict(p)
            q["assignment"] = _assign(wn, family)
            clean.append(q)
        if not clean:
            skipped["no_ir"] += 1
            continue
        molecules.append(
            {
                "folder": folder,
                "name": rec.get("name") or rec.get("compound_label") or folder,
                "formula": rec.get("formula"),
                "category": rec.get("category"),
                "subclass": rec.get("subclass"),
                "family": family,
                "source": source,
                "smiles": (feat or {}).get("smiles"),
                "peaks": clean,
            }
        )

    by_fam = defaultdict(list)
    for m in molecules:
        by_fam[m["family"]].append(m)

    families = {}
    overlay = {}
    for fam, rows in sorted(by_fam.items()):
        cons = _consensus(rows)
        proto = None
        for prefer in (
            "22-1-propanol",
            "23-2-propanol",
            "08-ethanol",
            "317-propionic-acid",
            "10-acetic-acid",
            "423-acetone",
            "11-ethyl-acetate",
            "78-propionaldehyde",
            "43-glycerol",
            "07-1-bromobutane",
        ):
            proto = next((r for r in rows if r["folder"] == prefer), None)
            if proto:
                break
        families[fam] = {
            "n": len(rows),
            "consensus": cons,
            "prototype": None if proto is None else proto["folder"],
        }
        ov = _overlay_for(fam, cons, proto)
        if ov:
            overlay[fam] = ov

    # Hard guarantee: 1-propanol CH2 scissor from Luna, even if consensus missed it.
    if "primary_alcohol" not in overlay:
        overlay["primary_alcohol"] = []
    if not any(b["id"] == "CH2_scissor" for b in overlay["primary_alcohol"]):
        overlay["primary_alcohol"].append(
            {
                "id": "CH2_scissor",
                "wn": 1465.0,
                "wn_range": [1440.0, 1475.0],
                "Tmin": 26.0,
                "fwhm": 80.0,
                "shape": "rounded",
                "source_family": "primary_alcohol",
                "exam_T_before": 83.2,
            }
        )
    if "ethanol" not in overlay:
        overlay["ethanol"] = []
    if not any(b["id"] == "CH2_scissor" for b in overlay["ethanol"]):
        overlay["ethanol"].append(
            {
                "id": "CH2_scissor",
                "wn": 1455.0,
                "wn_range": [1440.0, 1475.0],
                "Tmin": 53.0,
                "fwhm": 70.0,
                "shape": "rounded",
                "source_family": "ethanol",
                "exam_T_before": 83.2,
            }
        )

    doc = {
        "schema": "aliphatic_experimental_peaks.v1",
        "scope": "aliphatic acyclic experimental IR (SDBS liquid film)",
        "note": (
            "Luna encodings are preferred. GIF minima lists are not used "
            "(3850 cm⁻¹ axis ink). Overlay bands are diagnostic troughs the "
            "9701 exam-class envelope omitted (notably 1-alkanol CH2 ~1465)."
        ),
        "n_molecules": len(molecules),
        "skipped": skipped,
        "n_families": len(families),
        "families": families,
        "overlay_bands": overlay,
        "differentiation": {
            "propan-1-ol": {
                "smiles": "CCCO",
                "template_key": "primary_alcohol",
                "rule": "RDKit SMARTS [CH2][OX2H] → alcohol_template_key primary_alcohol",
                "diagnostic": [
                    "O-H alcohol 3200–3550, broad",
                    "CH2 scissor 1440–1475, rounded (experimental Tmin ~26; exam gold omitted this)",
                    "CH3 bend 1360–1390, moderate",
                    "C-O 1° 1000–1085, strong",
                ],
            },
            "propan-2-ol": {
                "smiles": "CC(C)O",
                "template_key": "secondary_alcohol",
                "rule": "RDKit SMARTS [CH1]([#6])[OX2H] without primary_alcohol → secondary_alcohol",
                "diagnostic": [
                    "O-H alcohol 3200–3550, broad",
                    "CH2/CH3 deformation ~1465 present",
                    "isopropyl CH3 1360–1390, strong (deeper than 1-ol)",
                    "C-O 2° 1085–1160, strong (exam gold sat at baseline here; overlay restores it)",
                    "no 1° C-O near 1050",
                ],
            },
        },
        "molecules": molecules,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    doc = build()
    print("wrote", OUT, "n", doc["n_molecules"], "families", doc["n_families"])
    print("skipped", doc["skipped"])
    for fam, rec in doc["families"].items():
        labs = [c["assignment"] for c in rec["consensus"]]
        print(f"  {fam:20} n={rec['n']:3}  {labs}")
    print("overlay")
    for fam, bands in doc["overlay_bands"].items():
        print(" ", fam, [(b["id"], b["wn"], b["Tmin"]) for b in bands])
