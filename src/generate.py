"""Structure → exam-grain spectra. Bond-true rules; never invent environments."""
from __future__ import annotations

from collections import defaultdict

from rdkit import Chem

from features import features as mol_features
from irsp_engine import family_of, irsp_curve
from nmr_aromatic import carbon_peaks as aromatic_c_peaks
from nmr_aromatic import proton_aromatic_ppm


def generate(smiles: str, name: str | None = None) -> dict:
    feat = mol_features(smiles)
    if not feat.get("aliphatic_acyclic"):
        raise ValueError(
            "Aliphatic acyclic generator only: this SMILES has a ring or aromatic atom. "
            "Use an open-chain aliphatic structure (e.g. CCCO, CC(=O)O, CCOC(=O)C)."
        )
    mol = Chem.AddHs(Chem.MolFromSmiles(feat["smiles"]))
    ir = ir_spectrum(feat)
    curve, irsp_meta = irsp_curve(feat)
    ir.update(irsp_meta)
    ir["curve"] = curve
    ir["family"] = family_of(feat)
    return {
        "name": name,
        "smiles": feat["smiles"],
        "formula": feat["formula"],
        "mw": feat["mw"],
        "features": feat,
        "ir": ir,
        "ms": ms_spectrum(feat),
        "hnmr": hnmr_spectrum(mol, feat),
        "cnmr": cnmr_spectrum(mol, feat),
        "identifiable": identifiable_tags(feat),
    }


def ir_spectrum(feat: dict) -> dict:
    f = feat["flags"]
    bands = []

    def add(bid, center, width, depth, shape="sharp"):
        bands.append(
            {"id": bid, "center": center, "width": width, "depth": depth, "shape": shape}
        )

    # Coexisting groups are additive (acid + alcohol both shown).
    if f.get("carboxylic_acid"):
        add("O-H_acid", 3000, 1100, 82, "very_broad")
        add("C=O_acid", 1710, 55, 88, "sharp")
        add("C-O_acid", 1260, 70, 62, "sharp")
    if f.get("alcohol_OH"):
        add("O-H_alcohol", 3330, 420, 85, "broad")
        if f.get("secondary_alcohol") and not f.get("primary_alcohol"):
            add("C-O_secondary", 1130, 80, 82, "sharp")
            add("CH3_isopropyl", 1375, 40, 55, "sharp")
            add("CH2_scissor", 1465, 55, 40, "rounded")
        else:
            add("C-O_primary", 1050, 90, 82, "sharp")
            add("CH2_scissor", 1465, 55, 50, "rounded")
            add("CH3_bend", 1380, 40, 32, "sharp")
    if f.get("phenol_OH"):
        add("O-H_phenol", 3350, 280, 72, "broad")
        add("C-O_phenol", 1220, 60, 55, "sharp")
    if f.get("ether") and not f.get("ester"):
        add("C-O_ether", 1120, 80, 60, "sharp")
    if f.get("acid_chloride"):
        add("C=O_acid_chloride", 1800, 45, 88, "sharp")
    if f.get("anhydride"):
        add("C=O_anhydride_a", 1820, 40, 80, "sharp")
        add("C=O_anhydride_b", 1760, 40, 80, "sharp")
    if f.get("ester"):
        add("C=O_ester", 1740, 50, 88, "sharp")
        add("C-O_ester_a", 1240, 70, 72, "sharp")
        add("C-O_ester_b", 1050, 70, 62, "sharp")
    if f.get("aldehyde"):
        add("C=O_aldehyde", 1730, 50, 86, "sharp")
        add("C-H_aldehyde", 2720, 40, 38, "sharp")
    if f.get("ketone"):
        add("C=O_ketone", 1715, 50, 88, "sharp")
    if f.get("amide"):
        add("C=O_amide", 1660, 55, 80, "sharp")
    if f.get("nitrile"):
        add("C≡N", 2250, 30, 48, "sharp")
    if f.get("alkyne_terminal"):
        add("≡C-H", 3310, 30, 52, "sharp")
        add("C≡C", 2120, 30, 28, "sharp")
    elif f.get("alkyne"):
        add("C≡C", 2120, 30, 22, "sharp")
    if f.get("alkene"):
        add("C=C", 1640, 40, 32, "sharp")
        if feat.get("n_vinyl_H"):
            add("alkene_oop", 910, 50, 45, "sharp")
    if f.get("aromatic"):
        add("C=C_aromatic", 1600, 35, 28, "sharp")
        if feat.get("n_arom_H"):
            add("C-H_sp2", 3030, 45, 32, "sharp")
            add("aromatic_oop", 750, 55, 48, "sharp")
    if f.get("nitro"):
        add("NO2_as", 1530, 45, 70, "sharp")
        add("NO2_s", 1350, 45, 70, "sharp")
    if f.get("primary_amine"):
        add("N-H_primary_a", 3370, 50, 36, "medium_broad")
        add("N-H_primary_b", 3450, 50, 36, "medium_broad")
    elif f.get("secondary_amine"):
        add("N-H_secondary", 3320, 50, 34, "medium_broad")
    if f.get("amide_NH"):
        add("N-H_amide", 3300, 80, 40, "medium_broad")
    if f.get("CCl") and not f.get("acid_chloride"):
        add("C-Cl", 700, 50, 42, "sharp")
    if f.get("CBr"):
        add("C-Br", 600, 50, 38, "sharp")
    if feat.get("n_sp3_CH"):
        add("C-H_sp3", 2930, 110, 58, "sharp")

    return {
        "type": "ir",
        "x": {"min": 400, "max": 4000, "dir": "reverse", "label": "wavenumber / cm$^{-1}$"},
        "y": {"min": 0, "max": 100, "label": "transmittance / \\%"},
        "bands": bands,
        "fingerprint_envelope": "none",
    }


def ms_spectrum(feat: dict) -> dict:
    m = feat["mw_int"]
    f = feat["flags"]
    peaks = [{"mz": m, "intensity": 35, "id": "M+"}]
    nC, nH = feat["n_C"], feat["n_H"]

    def add(mz, inten, pid):
        if mz < 15 or mz > m:
            return
        # crude formula budget: ion cannot exceed parent C/H
        peaks.append({"mz": int(mz), "intensity": inten, "id": pid})

    if f.get("primary_alcohol"):
        add(31, 100, "CH2OH+")
        add(m - 1, 40, "M-H")
    elif f.get("secondary_alcohol"):
        add(45, 100, "CH3CHOH+")
        add(m - 15, 40, "M-CH3")
    elif f.get("tertiary_alcohol"):
        add(59, 100, "Me2COH+")
        add(m - 15, 50, "M-CH3")
    if f.get("acetyl") and nC >= 2:
        add(43, 80, "CH3CO+")
    if (f.get("benzyl_CH2") or f.get("methyl_arene")) and nC >= 7 and nH >= 7:
        add(91, 100, "tropylium")
        add(65, 25, "C5H5")
    if f.get("carboxylic_acid"):
        add(45, 55, "COOH+")
        add(m - 17, 30, "M-OH")
    if feat["n_Cl"] == 1:
        peaks[0]["intensity"] = 100
        add(m + 2, 32, "M+2_Cl")
    elif feat["n_Cl"] >= 2:
        add(m + 2, 23, "M+2_Cl2")
        add(m + 4, 4, "M+4_Cl2")
    if feat["n_Br"] == 1:
        peaks[0]["intensity"] = 50
        add(m + 2, 50, "M+2_Br")
    elif feat["n_Br"] >= 2:
        add(m + 2, 100, "M+2_Br2")
        add(m + 4, 50, "M+4_Br2")
        peaks[0]["intensity"] = 50

    by = {}
    for p in peaks:
        old = by.get(p["mz"])
        if old is None or p["intensity"] > old["intensity"]:
            by[p["mz"]] = p
    sticks = sorted(by.values(), key=lambda x: x["mz"])
    mx = max(p["intensity"] for p in sticks) if sticks else 1
    if mx < 100:
        for p in sticks:
            p["intensity"] = int(round(p["intensity"] * 100 / mx))
    return {
        "type": "ms",
        "x": {"label": "m/z"},
        "y": {"label": "relative intensity", "max": 100},
        "peaks": sticks,
    }


def _h_class(h, mol) -> tuple[str, float]:
    """Return (label, exam delta) for a hydrogen atom."""
    neigh = h.GetNeighbors()
    if not neigh:
        return "H", 0.0
    x = neigh[0]
    sym = x.GetSymbol()
    if sym == "O":
        # carboxylic vs alcohol
        for n2 in x.GetNeighbors():
            if n2.GetIdx() == h.GetIdx():
                continue
            if n2.GetSymbol() == "C":
                if any(b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(n2).GetSymbol() == "O"
                       for b in n2.GetBonds()):
                    return "COOH", 11.5
        return "OH", 2.3
    if sym == "N":
        return "NH", 1.5
    if sym != "C":
        return "XH", 3.0
    # carbon-bound H
    nH_on_C = sum(1 for n in x.GetNeighbors() if n.GetSymbol() == "H")
    if x.GetIsAromatic():
        arom = getattr(hnmr_spectrum, "_arom_h", {}) or {}
        return "ArH", round(float(arom.get(h.GetIdx(), 7.3)), 2)
    # aldehyde: carbon with one H and C=O
    if nH_on_C == 1 and any(
        b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(x).GetSymbol() == "O" for b in x.GetBonds()
    ):
        return "CHO", 9.7
    # vinyl
    if any(b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(x).GetSymbol() == "C" for b in x.GetBonds()):
        return "vinyl", 5.4
    # next to O
    if any(b.GetOtherAtom(x).GetSymbol() == "O" for b in x.GetBonds()):
        return "CH-O", 3.7
    # next to C=O
    for b in x.GetBonds():
        o = b.GetOtherAtom(x)
        if o.GetSymbol() == "C" and any(
            bb.GetBondType() == Chem.BondType.DOUBLE and bb.GetOtherAtom(o).GetSymbol() == "O" for bb in o.GetBonds()
        ):
            return "CH-C=O", 2.2
    # next to aromatic
    if any(b.GetOtherAtom(x).GetIsAromatic() for b in x.GetBonds()):
        return "ArCH3", 2.3
    return "alkyl", 1.2


def _nplus1(h, mol) -> str:
    """First-order multiplicity from H on neighbouring carbons (ignore OH/NH)."""
    c = h.GetNeighbors()[0]
    if c.GetSymbol() != "C":
        return "s"
    nH = 0
    for o in c.GetNeighbors():
        if o.GetIdx() == h.GetIdx():
            continue
        if o.GetSymbol() == "C":
            nH += sum(1 for n in o.GetNeighbors() if n.GetSymbol() == "H")
    return {0: "s", 1: "d", 2: "t", 3: "q"}.get(nH, "m")


def hnmr_spectrum(mol, feat: dict) -> dict:
    hnmr_spectrum._arom_h = proton_aromatic_ppm(mol)
    groups = defaultdict(lambda: {"H": 0, "mult": "s", "delta": 0.0, "id": ""})
    ranks = list(Chem.CanonicalRankAtoms(mol, breakTies=False))
    for atom in mol.GetAtoms():
        if atom.GetSymbol() != "H":
            continue
        lab, delta = _h_class(atom, mol)
        attached = atom.GetNeighbors()[0].GetIdx()
        key = (lab, ranks[attached])
        g = groups[key]
        g["H"] += 1
        g["delta"] = delta
        g["id"] = lab
        if lab in {"OH", "NH", "COOH", "CHO"}:
            g["mult"] = "s"
        elif lab == "ArH":
            g["mult"] = "m"
        else:
            g["mult"] = _nplus1(atom, mol)
    peaks = [
        {"delta": g["delta"], "mult": g["mult"], "H": g["H"], "id": g["id"]}
        for g in groups.values()
        if g["H"]
    ]
    peaks.sort(key=lambda p: p["delta"])
    return {
        "type": "hnmr",
        "x": {"min": 0, "max": 12, "dir": "reverse", "label": "$\\delta$ / ppm"},
        "peaks": peaks,
    }


def cnmr_spectrum(mol, feat: dict) -> dict:
    bare = Chem.RemoveHs(mol)
    arom_idx = {a.GetIdx() for a in bare.GetAtoms() if a.GetIsAromatic() and a.GetSymbol() == "C"}
    peaks = aromatic_c_peaks(bare) if arom_idx else []
    ranks = list(Chem.CanonicalRankAtoms(bare, breakTies=False))
    seen = set()
    for atom, r in zip(bare.GetAtoms(), ranks):
        if atom.GetSymbol() != "C" or atom.GetIdx() in arom_idx:
            continue
        if r in seen:
            continue
        seen.add(r)
        peaks.append({"delta": _c_shift(atom), "id": f"C{r}"})
    peaks.sort(key=lambda p: -float(p["delta"]))
    return {
        "type": "cnmr",
        "x": {"min": 0, "max": 220, "dir": "reverse", "label": "$\\delta$ / ppm"},
        "peaks": peaks,
    }


def _c_shift(atom) -> int:
    if atom.GetIsAromatic():
        if any(b.GetOtherAtom(atom).GetSymbol() == "O" for b in atom.GetBonds()):
            return 155
        return 128
    # carbonyl
    for b in atom.GetBonds():
        if b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(atom).GetSymbol() == "O":
            others = [bb.GetOtherAtom(atom).GetSymbol() for bb in atom.GetBonds() if bb.GetIdx() != b.GetIdx()]
            if "O" in others:
                return 177  # acid/ester
            if "Cl" in others:
                return 170
            if "N" in others:
                return 170
            if atom.GetTotalNumHs() == 1:
                return 202  # aldehyde
            return 207  # ketone
    # nitrile
    for b in atom.GetBonds():
        if b.GetBondType() == Chem.BondType.TRIPLE and b.GetOtherAtom(atom).GetSymbol() == "N":
            return 118
    # alkyne
    for b in atom.GetBonds():
        if b.GetBondType() == Chem.BondType.TRIPLE and b.GetOtherAtom(atom).GetSymbol() == "C":
            return 80
    # alkene
    for b in atom.GetBonds():
        if b.GetBondType() == Chem.BondType.DOUBLE and b.GetOtherAtom(atom).GetSymbol() == "C":
            return 122
    # C-O
    if any(b.GetOtherAtom(atom).GetSymbol() == "O" for b in atom.GetBonds()):
        return 62
    # C-X
    if any(b.GetOtherAtom(atom).GetSymbol() in {"Cl", "Br", "I"} for b in atom.GetBonds()):
        return 35
    return 22


def identifiable_tags(feat: dict) -> dict:
    f = feat["flags"]
    ir = []
    if f.get("carboxylic_acid"):
        ir += ["broad_OH_2500_3300", "C=O_~1700"]
    if f.get("alcohol_OH"):
        ir.append("broad_OH_~3300")
    if f.get("phenol_OH"):
        ir.append("broad_OH_~3300")
    carbons = feat.get("carbonyls") or []
    if carbons:
        ir.append("C=O")
        if "ester" in carbons:
            ir.append("C-O_ester")
        if "aldehyde" in carbons:
            ir.append("aldehyde_CH")
        if "carboxylic_acid" in carbons:
            ir.append("C=O_~1700")
    elif not f.get("carboxylic_acid"):
        ir.append("no_C=O")
    if f.get("nitrile"):
        ir.append("C≡N_~2250")
    if f.get("alkene") and not f.get("aromatic"):
        ir.append("C=C")
    oh = None
    if f.get("carboxylic_acid"):
        oh = "acid"
    elif f.get("alcohol_OH"):
        oh = "alcohol"
    elif f.get("phenol_OH"):
        oh = "phenol"
    return {
        "ir": ir,
        "has_OH": oh is not None,
        "has_carbonyl": bool(carbons),
        "oh_class": oh,
        "carbonyl_class": feat.get("carbonyl_class"),
        "carbonyls": carbons,
    }
