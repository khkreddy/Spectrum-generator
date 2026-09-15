"""IRSP-2.5 dual-zone IR. Shared family parameters (fitted); SMILES only at inference."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from luna_ir_templates import T_template, acid_template_key, alcohol_template_key
from render_tikz import render_ir_from_curve

WN = list(range(4000, 399, -4))
_ROOT = Path(__file__).resolve().parents[1]
FITTED = _ROOT / "data" / "rules" / "irsp_fitted.json"
EXPERIMENTAL = _ROOT / "data" / "rules" / "aliphatic_experimental_peaks.json"
_OVERLAY: dict | None = None

# Priors from IRSP-2.5 / exam grain. Fit may overwrite.
DEFAULTS = {
    "alcohol": {
        "baseline": 90.0,
        "oh_nu": 3330.0,
        "oh_sig": 150.0,
        "oh_amp": 82.0,
        "ch": [[2960, 10, 70], [2925, 10, 78], [2870, 10, 55]],
        "co_nu": 1055.0,
        "co_g": 18.0,
        "co_a": 78.0,
        "jag_n": 8,
        "jag_amp": 10.0,
    },
    "ketone": {
        "baseline": 90.0,
        "oh_amp": 0.0,
        "ch": [[2965, 10, 22], [2920, 10, 28], [2870, 10, 18]],
        "co_nu": 1715.0,
        "co_g": 11.0,
        "co_a": 88.0,
        "fpr_nu": 1220.0,
        "fpr_g": 16.0,
        "fpr_a": 42.0,
        "jag_n": 7,
        "jag_amp": 9.0,
    },
    "acid": {
        "baseline": 91.0,
        "jag_n": 8,
        "jag_amp": 8.0,
    },
    "aldehyde": {
        "baseline": 91.0,
        "ch": [[2960, 10, 24], [2920, 10, 28], [2870, 10, 18]],
        "co_nu": 1730.0,
        "co_g": 12.0,
        "co_a": 82.0,
        "cho_nu": 2720.0,
        "cho_g": 9.0,
        "cho_a": 30.0,
        "jag_n": 5,
        "jag_amp": 7.0,
    },
    "ester": {
        "baseline": 91.0,
        "ch": [[2980, 10, 22], [2940, 10, 28], [2875, 10, 16]],
        "co_nu": 1742.0,
        "co_g": 11.0,
        "co_a": 84.0,
        "co1_nu": 1240.0,
        "co1_a": 62.0,
        "co2_nu": 1050.0,
        "co2_a": 52.0,
        "jag_n": 6,
        "jag_amp": 7.0,
    },
    "alkyl_halide": {
        "baseline": 92.0,
        "ch": [[2960, 10, 40], [2930, 10, 48], [2870, 10, 28]],
        "cx_nu": 650.0,
        "cx_g": 22.0,
        "cx_a": 40.0,
        "jag_n": 5,
        "jag_amp": 8.0,
    },
}


def _gauss(nu, nu0, sigma, amp):
    return amp * math.exp(-0.5 * ((nu - nu0) / max(1.0, sigma)) ** 2)


def _agauss(nu, nu0, sigma, amp, high_scale=0.72, low_scale=1.15):
    """Asymmetric Gaussian: steeper on the high-wavenumber side (no junk above 3500)."""
    s = sigma * (high_scale if nu >= nu0 else low_scale)
    return amp * math.exp(-0.5 * ((nu - nu0) / max(1.0, s)) ** 2)


def _lorentz(nu, nu0, gamma, amp):
    x = (nu - nu0) / max(1.0, gamma)
    return amp / (1.0 + x * x)


def _super_gauss(nu, nu0, sigma, amp, n=4):
    return amp * math.exp(-((abs(nu - nu0) / max(1.0, sigma)) ** n))


def _seed(smiles: str) -> int:
    return int(hashlib.sha256((smiles or "irsp").encode()).hexdigest()[:8], 16)


def family_of(feat: dict) -> str:
    f = feat.get("flags") or {}
    carbons = feat.get("carbonyls") or []
    if f.get("carboxylic_acid"):
        return "acid"
    if f.get("ester") or "ester" in carbons:
        return "ester"
    if "aldehyde" in carbons:
        return "aldehyde"
    if "ketone" in carbons or "acid_chloride" in carbons:
        return "ketone"
    n_oh = int(bool(f.get("primary_alcohol"))) + int(bool(f.get("secondary_alcohol"))) + int(bool(f.get("alcohol_OH")))
    if f.get("alcohol_OH") or f.get("phenol_OH"):
        return "alcohol"
    if f.get("CBr") or f.get("CCl"):
        return "alkyl_halide"
    return "alkyl_halide" if f.get("CBr") else "ketone"


def load_families() -> dict:
    if FITTED.is_file():
        try:
            d = json.loads(FITTED.read_text(encoding="utf-8"))
            fam = d.get("families") or {}
            out = {k: dict(DEFAULTS[k]) for k in DEFAULTS}
            for k, v in fam.items():
                if k in out and isinstance(v, dict):
                    out[k].update(v)
            return out
        except Exception:
            pass
    return {k: dict(v) for k, v in DEFAULTS.items()}


def carboxyl_env(feat: dict) -> dict:
    """Canonical carboxyl IR from SDBS/exam correlations, tweaked by environment.

    Experimental (propionic acid SDBS table): dimer O-H canyon 3000–2650 (T~10–38),
    C=O 1716 cm⁻¹ at 4 %T, C–O 1240 at 12 %T, dimer O–H oop ~933.
    Exam drawings: same bands, slightly lifted baseline, fingerprint kept.
    """
    f = feat.get("flags") or {}
    nC = int(feat.get("n_C") or 2)
    aryl = bool(f.get("aryl_acid"))
    acetic = bool(f.get("alpha_CH3_acid")) and nC == 2
    has_ch2 = bool(f.get("alpha_CH2_acid"))
    if aryl:
        co_nu, co_a = 1688.0, 82.0
        ch3_as, ch2, ch3_s = 0.0, 0.0, 0.0
        ar_ch = 16.0
    elif acetic:
        co_nu, co_a = 1716.0, 86.0
        ch3_as, ch2, ch3_s = 24.0, 6.0, 18.0
        ar_ch = 0.0
    else:
        co_nu, co_a = 1714.0, 84.0
        ch3_as, ch2, ch3_s = 14.0, 30.0, 12.0
        ar_ch = 0.0
    wing = 20.0 if (not aryl and nC >= 4) else 0.0
    return {
        "oh1_nu": 3040.0,
        "oh1_sig": 230.0 + wing,
        "oh1_amp": 70.0,
        "oh2_nu": 2660.0,
        "oh2_sig": 150.0 + 0.5 * wing,
        "oh2_amp": 44.0,
        "co_nu": co_nu,
        "co_g": 10.0,
        "co_a": co_a,
        "ch3_as": ch3_as,
        "ch2": ch2,
        "ch3_s": ch3_s,
        "ar_ch": ar_ch,
        "bend_1415": 26.0 if has_ch2 else (18.0 if acetic else 16.0),
        "co_stretch_nu": 1290.0 if acetic else 1240.0,
        "co_stretch_a": 48.0 if acetic else 56.0,
        "dimer_oop": 46.0,
        "jag_n": 8,
        "jag_amp": 7.0,
    }


def _T_acid(nu: float, env: dict, smiles: str) -> float:
    """Carboxyl: canyon O-H + C-H spikes (E) + sharp C=O + C-O + dimer oop."""
    t = 91.0
    t -= _super_gauss(nu, env["oh1_nu"], env["oh1_sig"], env["oh1_amp"], n=3)
    t -= _gauss(nu, env["oh2_nu"], env["oh2_sig"], env["oh2_amp"])
    t -= _lorentz(nu, 2962, 8, env["ch3_as"])
    t -= _lorentz(nu, 2935, 8, env["ch2"])
    t -= _lorentz(nu, 2878, 8, env["ch3_s"])
    if env.get("ar_ch"):
        t -= _lorentz(nu, 3030, 8, env["ar_ch"])
    t -= _lorentz(nu, env["co_nu"], env["co_g"], env["co_a"])
    t -= _lorentz(nu, 1415, 16, env["bend_1415"])
    t -= _lorentz(nu, env["co_stretch_nu"], 14, env["co_stretch_a"])
    t -= _lorentz(nu, 1080, 14, 22)
    t -= _lorentz(nu, 933, 20, env["dimer_oop"])
    rng = random.Random(_seed(smiles + ":acid"))
    for _ in range(int(env.get("jag_n", 8))):
        nu0 = rng.uniform(520, 1480)
        amp = rng.uniform(3.0, env.get("jag_amp", 7.0))
        t -= _lorentz(nu, nu0, rng.uniform(6, 14), amp)
    return max(3.0, min(96.0, t))


def _fpr_jags(nu: float, smiles: str, n: int, amp: float, lo: float = 520.0, hi: float = 1000.0) -> float:
    """Fingerprint texture only below 1000 cm-1 — never above 1500."""
    rng = random.Random(_seed(smiles + ":fpr"))
    t = 0.0
    for _ in range(n):
        nu0 = rng.uniform(lo, hi)
        t += _lorentz(nu, nu0, rng.uniform(6, 14), rng.uniform(0.35 * amp, amp))
    return t


def overlay_bands(key: str) -> list[dict]:
    """Diagnostic experimental bands the 9701 exam envelope omitted."""
    global _OVERLAY
    if _OVERLAY is None:
        if EXPERIMENTAL.is_file():
            try:
                _OVERLAY = json.loads(EXPERIMENTAL.read_text(encoding="utf-8")).get(
                    "overlay_bands"
                ) or {}
            except Exception:
                _OVERLAY = {}
        else:
            _OVERLAY = {}
    return _OVERLAY.get(key) or []


def _band_T(nu: float, band: dict) -> float:
    wn = float(band["wn"])
    tmin = float(band["Tmin"])
    fwhm = float(band.get("fwhm") or 80.0)
    shape = band.get("shape") or "rounded"
    baseline = 90.0
    amp = max(0.0, baseline - tmin)
    if shape == "broad":
        return baseline - _agauss(nu, wn, max(20.0, fwhm / 2.2), amp)
    if shape == "sharp":
        return baseline - _lorentz(nu, wn, max(8.0, fwhm / 2.5), amp)
    return baseline - _gauss(nu, wn, max(12.0, fwhm / 2.355), amp)


def apply_experimental_overlay(nu: float, T: float, key: str) -> float:
    for band in overlay_bands(key):
        T = min(T, _band_T(nu, band))
    return T


def T_at(nu: float, p: dict, family: str, smiles: str, feat: dict | None = None) -> float:
    feat = feat or {}
    f = feat.get("flags") or {}
    # Exam-class envelope first; experimental diagnostic bands fill gaps
    # the paper simplified away (1-alkanol CH2 ~1465, 2° C–O ~1130).
    if feat:
        luna_key = None
        if family == "alcohol":
            luna_key = alcohol_template_key(feat)
        elif family == "acid" and not f.get("aryl_acid"):
            luna_key = acid_template_key(feat)
        elif family == "ketone":
            luna_key = "ketone"
        elif family == "aldehyde":
            luna_key = "aldehyde"
        elif family == "ester":
            luna_key = "ester"
        elif family == "alkyl_halide":
            luna_key = "alkyl_bromide"
        if luna_key:
            tv = T_template(nu, luna_key)
            if tv is not None:
                tv = apply_experimental_overlay(nu, tv, luna_key)
                return max(3.0, min(96.0, tv))
    if family == "acid":
        env = p.get("_carboxyl") or carboxyl_env(feat)
        return _T_acid(nu, env, smiles)

    t = float(p.get("baseline", 91.0))
    if family == "alcohol":
        # Keep O-H off the 3600+ noise: modest σ, centre ~3350 (Luna ethanol basin).
        nC = int(feat.get("n_C") or 2)
        oh_nu = 3380.0 if nC >= 3 else 3345.0
        oh_sig = 92.0
        oh_amp = 78.0
        if f.get("secondary_alcohol"):
            oh_nu = 3370.0
            oh_amp = 80.0
        t -= _agauss(nu, oh_nu, oh_sig, oh_amp, high_scale=0.70, low_scale=1.18)
        # C-H multiplet on the low-wn shoulder (not isolated spikes)
        t -= _lorentz(nu, 2962, 9, 38 if f.get("primary_alcohol") else 48)
        t -= _lorentz(nu, 2930, 9, 32 if f.get("primary_alcohol") else 44)
        t -= _lorentz(nu, 2872, 9, 22 if f.get("primary_alcohol") else 30)
        # CH bends — fingerprint ~1400 (ethanol was too flat)
        t -= _lorentz(nu, 1458, 18, 34)
        t -= _lorentz(nu, 1382, 12, 26)
        # C-O split cluster (Luna ethanol 1075/1035; 1-propanol extra ~970)
        if f.get("secondary_alcohol"):
            t -= _lorentz(nu, 1120, 14, 55)
            t -= _lorentz(nu, 1075, 12, 62)
        else:
            t -= _lorentz(nu, 1075, 12, 50)
            t -= _lorentz(nu, 1035, 11, 72)
            if int(feat.get("n_C") or 0) >= 3:
                t -= _lorentz(nu, 970, 12, 40)
        t -= _fpr_jags(nu, smiles, 4, 6.0, 520, 900)
    elif family == "aldehyde":
        t -= _lorentz(nu, p["co_nu"], p["co_g"], p["co_a"])
        t -= _lorentz(nu, p["cho_nu"], p["cho_g"], p["cho_a"])
        for c, g, a in p["ch"]:
            t -= _lorentz(nu, c, g, a)
        t -= _lorentz(nu, 1410, 14, 16)
        t -= _fpr_jags(nu, smiles, 5, p.get("jag_amp", 7), 520, 1100)
    elif family == "ester":
        t -= _lorentz(nu, p["co_nu"], p["co_g"], p["co_a"])
        t -= _lorentz(nu, p["co1_nu"], 16, p["co1_a"])
        t -= _lorentz(nu, p["co2_nu"], 14, p["co2_a"])
        for c, g, a in p["ch"]:
            t -= _lorentz(nu, c, g, a)
        t -= _lorentz(nu, 1460, 14, 14)
        t -= _fpr_jags(nu, smiles, 5, p.get("jag_amp", 7), 520, 1000)
    elif family == "alkyl_halide":
        for c, g, a in p["ch"]:
            t -= _lorentz(nu, c, g, a)
        t -= _lorentz(nu, 1455, 16, 20)
        t -= _lorentz(nu, 1380, 12, 14)
        t -= _lorentz(nu, 1250, 18, 16)
        t -= _lorentz(nu, p.get("cx_nu", 650), p.get("cx_g", 22), p.get("cx_a", 40))
        t -= _fpr_jags(nu, smiles, 4, p.get("jag_amp", 8), 520, 900)
    else:  # ketone
        t -= _lorentz(nu, p.get("co_nu", 1715), p.get("co_g", 11), p.get("co_a", 88))
        for c, g, a in p.get("ch") or [[2965, 10, 22], [2920, 10, 28], [2870, 10, 18]]:
            t -= _lorentz(nu, c, g, a)
        t -= _lorentz(nu, 1360, 14, 20)
        t -= _lorentz(nu, p.get("fpr_nu", 1220), p.get("fpr_g", 16), p.get("fpr_a", 42))
        t -= _fpr_jags(nu, smiles, 5, p.get("jag_amp", 9), 520, 1100)
    return max(3.0, min(96.0, t))


def irsp_curve(feat: dict, families: dict | None = None) -> tuple[list[list[float]], dict]:
    fam = family_of(feat)
    p = dict((families or load_families())[fam])
    smiles = feat.get("smiles") or ""
    if fam == "alcohol" and feat.get("flags", {}).get("secondary_alcohol"):
        p["co_nu"] = float(p.get("co_nu_sec", 1110.0))
    if fam == "acid":
        p["_carboxyl"] = carboxyl_env(feat)
    curve = [[float(nu), round(T_at(nu, p, fam, smiles, feat), 2)] for nu in WN]
    meta = {"protocol": "IRSP-2.5-fitted", "family": fam, "n_samples": len(WN)}
    if fam == "acid":
        meta["carboxyl_env"] = {k: v for k, v in p["_carboxyl"].items() if not k.startswith("_")}
    return curve, meta


def render_irsp(feat: dict, families: dict | None = None) -> str:
    curve, _ = irsp_curve(feat, families)
    return render_ir_from_curve(curve, step_wn=8.0)
