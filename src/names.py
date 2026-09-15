"""Resolve a typed molecule (name, formula, or SMILES) to SMILES. No LLM."""
from __future__ import annotations

import json
import re
from pathlib import Path

from rdkit import Chem

ROOT = Path(__file__).resolve().parents[1]

SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁺⁻", "0123456789+-")

EXTRA = {
    "ethanol": "CCO",
    "ethanoic acid": "CC(=O)O",
    "acetic acid": "CC(=O)O",
    "ethyl ethanoate": "CCOC(=O)C",
    "ethyl acetate": "CCOC(=O)C",
    "ethylethanoate": "CCOC(=O)C",
    "methyl ethanoate": "COC(=O)C",
    "methyl acetate": "COC(=O)C",
    "propanone": "CC(=O)C",
    "acetone": "CC(=O)C",
    "propanal": "CCC=O",
    "propan-1-ol": "CCCO",
    "propan-2-ol": "CC(C)O",
    "propanoic acid": "CCC(=O)O",
    "butan-1-ol": "CCCCO",
    "butan-2-ol": "CCC(C)O",
    "butanone": "CCC(=O)C",
    "butan-2-one": "CCC(=O)C",
    "butanoic acid": "CCCC(=O)O",
    "hydroxyacetone": "CC(=O)CO",
    "3-hydroxybutanal": "CC(O)CC=O",
    "but-3-en-1-ol": "C=CCCO",
    "cyclobutanol": "OC1CCC1",
    "glycerol": "OCC(O)CO",
    "benzaldehyde": "O=Cc1ccccc1",
    "toluene": "Cc1ccccc1",
    "aniline": "Nc1ccccc1",
    "phenol": "Oc1ccccc1",
    "1-bromobutane": "CCCCBr",
    "cyclohexene": "C1CCC=CC1",
    "acetyl chloride": "CC(=O)Cl",
    "nitrobenzene": "O=[N+]([O-])c1ccccc1",
    "hexane": "CCCCCC",
    "n-hexane": "CCCCCC",
    "cyclohexane": "C1CCCCC1",
    "1-hexyne": "CCCCC#C",
    "chlorobenzene": "Clc1ccccc1",
    "benzene": "c1ccccc1",
    "methanol": "CO",
    "ethene": "C=C",
    "ethyne": "C#C",
    "ch3ch2oh": "CCO",
    "ch3ch2cho": "CCC=O",
    "ch3ch2co2h": "CCC(=O)O",
    "ch3ch2ch2oh": "CCCO",
    "ch3ch(oh)ch3": "CC(C)O",
    "ch3coch3": "CC(=O)C",
    "ch3co2ch3": "COC(=O)C",
    "ch3coch2oh": "CC(=O)CO",
    "ch3co2h": "CC(=O)O",
    "ch3ch2co2ch3": "CCC(=O)OC",
}


def _norm(s: str) -> str:
    t = (s or "").strip().translate(SUB)
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"\s+", " ", t)
    return t.lower()


def _load_catalog() -> dict[str, str]:
    out = dict(EXTRA)
    p = ROOT / "data" / "molecules.json"
    if p.is_file():
        doc = json.loads(p.read_text(encoding="utf-8"))
        for bucket in ("canary", "exam_9701"):
            for m in doc.get(bucket) or []:
                smi = m.get("smiles")
                if not smi:
                    continue
                if m.get("name"):
                    out[_norm(m["name"])] = smi
                if m.get("id"):
                    out[_norm(m["id"].replace("_", " "))] = smi
                    out[_norm(m["id"].replace("_", "-"))] = smi
                for a in m.get("aliases") or []:
                    out[_norm(a)] = smi
                    out[_norm(a.replace(" ", ""))] = smi
    return out


CATALOG = _load_catalog()


def resolve(text: str) -> dict:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty molecule")
    key = _norm(raw)
    key_ns = key.replace(" ", "").replace("-", "")
    smi = CATALOG.get(key) or CATALOG.get(key_ns)
    if not smi:
        mol = Chem.MolFromSmiles(raw)
        if mol is None:
            raise ValueError(f"unknown molecule: {raw}")
        smi = Chem.MolToSmiles(mol)
        name = raw
    else:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            raise ValueError(f"bad stored SMILES for {raw}")
        smi = Chem.MolToSmiles(mol)
        name = raw
    return {"name": name, "smiles": smi, "input": raw}
