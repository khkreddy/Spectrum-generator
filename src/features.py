"""RDKit features from SMILES. Bond-true flags; no exam-plot fitting."""
from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

SMARTS = {
    "alcohol_OH": "[CX4][OX2H]",
    "phenol_OH": "[c][OX2H]",
    "carboxylic_acid": "[CX3](=O)[OX2H1]",
    "aryl_acid": "[c][CX3](=O)[OX2H1]",
    "alpha_CH2_acid": "[CH2][CX3](=O)[OX2H1]",
    "alpha_CH3_acid": "[CH3][CX3](=O)[OX2H1]",
    "ester": "[CX3](=O)[OX2][#6]",
    "aldehyde": "[CX3H1](=O)[#6]",
    "ketone": "[#6][CX3](=O)[#6]",
    "acid_chloride": "[CX3](=O)[Cl]",
    "amide": "[CX3](=O)[NX3]",
    "amide_NH": "[CX3](=O)[NX3;H1,H2]",
    "primary_amine": "[NX3;H2][#6]",
    "secondary_amine": "[NX3;H1]([#6])[#6]",
    "nitrile": "[CX2]#[NX1]",
    "nitro": "[N+](=O)[O-]",
    "alkene": "[CX3]=[CX3]",
    "alkyne_terminal": "[CX2]#[CX2H]",
    "alkyne": "[CX2]#[CX2]",
    "aromatic": "a",
    "ether": "[OD2]([#6])[#6]",
    "CCl": "[#6][Cl]",
    "CBr": "[#6][Br]",
    "CI": "[#6][I]",
    "primary_alcohol": "[CH2][OX2H]",
    "secondary_alcohol": "[CH1]([#6])[OX2H]",
    "tertiary_alcohol": "[CX4]([#6])([#6])([#6])[OX2H]",
    "acetyl": "[CH3][CX3](=O)",
    "benzyl_CH2": "[CH2]c",
    "methyl_arene": "[CH3]c",
    "sp3_CH": "[CX4!H0]",
    "arom_H": "[cH]",
    "vinyl_H": "[CX3;!H0]=[#6]",
    "anhydride": "[CX3](=O)[OX2][CX3](=O)",
}

ISO = {"H": 1, "C": 12, "N": 14, "O": 16, "F": 19, "Si": 28, "P": 31, "S": 32, "Cl": 35, "Br": 79, "I": 127}


def _has(mol, smarts: str) -> bool:
    q = Chem.MolFromSmarts(smarts)
    return bool(q and mol.HasSubstructMatch(q))


def _n(mol, smarts: str) -> int:
    q = Chem.MolFromSmarts(smarts)
    if not q:
        return 0
    return len(mol.GetSubstructMatches(q))


def _nominal(mol) -> int:
    return sum(ISO.get(a.GetSymbol(), int(round(a.GetMass()))) for a in mol.GetAtoms())


def _carbonyls(flags: dict) -> list[str]:
    order = [
        "anhydride",
        "acid_chloride",
        "carboxylic_acid",
        "ester",
        "amide",
        "aldehyde",
        "ketone",
    ]
    return [k for k in order if flags.get(k)]


def features(smiles: str) -> dict:
    mol0 = Chem.MolFromSmiles(smiles)
    if mol0 is None:
        raise ValueError(f"unparseable SMILES: {smiles}")
    mol = Chem.AddHs(mol0)
    flags = {k: _has(mol, s) for k, s in SMARTS.items()}
    if flags["carboxylic_acid"]:
        n_ester = _n(mol, SMARTS["ester"])
        n_acid = _n(mol, SMARTS["carboxylic_acid"])
        flags["ester"] = n_ester > n_acid
    n_ar = sum(1 for a in mol.GetAtoms() if a.GetIsAromatic())
    n_rings = int(mol0.GetRingInfo().NumRings())
    carbons = _carbonyls(flags)
    return {
        "smiles": Chem.MolToSmiles(Chem.RemoveHs(mol)),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": round(Descriptors.MolWt(mol), 2),
        "mw_int": _nominal(mol),
        "n_C": sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "C"),
        "n_H": sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "H"),
        "n_Cl": sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "Cl"),
        "n_Br": sum(1 for a in mol.GetAtoms() if a.GetSymbol() == "Br"),
        "n_sp3_CH": _n(mol, SMARTS["sp3_CH"]),
        "n_arom_H": _n(mol, SMARTS["arom_H"]),
        "n_vinyl_H": _n(mol, SMARTS["vinyl_H"]),
        "aromatic_atoms": n_ar,
        "n_rings": n_rings,
        "aliphatic_acyclic": n_ar == 0 and n_rings == 0,
        "flags": flags,
        "distinct_C": _distinct_carbon_count(mol),
        "carbonyls": carbons,
        "carbonyl_class": carbons[0] if carbons else None,
    }


def _distinct_carbon_count(mol) -> int:
    bare = Chem.RemoveHs(mol)
    try:
        ranks = Chem.CanonicalRankAtoms(bare, breakTies=False)
    except Exception:
        return sum(1 for a in bare.GetAtoms() if a.GetSymbol() == "C")
    return len({r for a, r in zip(bare.GetAtoms(), ranks) if a.GetSymbol() == "C"})
