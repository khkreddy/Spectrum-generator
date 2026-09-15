"""Exam-grain TikZ. Native tikz only (TikZJax). Axis grammar from 9701 IR/MS."""
from __future__ import annotations

import json
import math
from pathlib import Path


def render_all(spec: dict) -> dict:
    """IR from the aliphatic exam-class envelope. Do not splice SDBS peak tables:

    those tables list trough vertices only, so 4000→2986 becomes a sharp V at
    3000 instead of the carboxylic acid OH canyon (2500–3300).
    """
    try:
        from irsp_engine import render_irsp
        ir_tikz = render_irsp(spec.get("features") or {})
    except Exception:
        ir_tikz = render_ir(spec["ir"])
    return {
        "ir": ir_tikz,
        "ms": render_ms(spec["ms"]),
        "hnmr": render_hnmr(spec["hnmr"]),
        "cnmr": render_cnmr(spec["cnmr"]),
    }


def render_ir_from_peak_table(peaks: list, baseline: float = 92.0) -> str:
    """Envelope through experimental (wn, %T) vertices plus baseline recoveries.

    This is how SDBS peak tables become an exam-style IR: keep every listed
    trough and the recoveries between them, not four Gaussians on a flat line.
    """
    pts = sorted(((float(wn), float(T)) for wn, T in peaks), key=lambda p: -p[0])
    env = [(4000.0, baseline)]
    for wn, T in pts:
        # recovery toward baseline before a trough if the gap is large
        if env and env[-1][0] - wn > 180 and env[-1][1] < baseline - 5:
            mid = (env[-1][0] + wn) / 2
            env.append((mid, min(baseline, env[-1][1] + 25)))
        env.append((wn, max(2.0, min(98.0, T))))
    if env[-1][0] > 420:
        env.append((400.0, baseline))
    coords = " ".join(f"({wn:.0f},{T:.1f})" for wn, T in env)
    return (
        r"\begin{tikzpicture}[x=-0.00205cm,y=0.048cm,font=\sffamily\small,line cap=round,line join=round]"
        r"\draw (4000,0)--(4000,100)--(400,100)--(400,0)--cycle;"
        r"\foreach \x/\t in {4000/4000,3000/3000,2000/2000,1500/1500,1000/1000,500/500}"
        r"{\draw (\x,0)--++(0,-2.2) node[below]{\t};}"
        r"\foreach \y/\t in {0/0,50/50,100/100}{\draw (4000,\y)--++(-45,0) node[left]{\t};}"
        r"\node[align=center] at (4680,50){transmittance\\/ \%};"
        r"\node at (2200,-14){wavenumber / cm$^{-1}$};"
        r"\draw[thick] plot[smooth] coordinates {" + coords + r"};"
        r"\end{tikzpicture}"
    )


def render_ir_from_curve(curve: list, step_wn: float = 8.0) -> str:
    """9701 two-scale native TikZ from a (wn, T) curve."""
    if not curve:
        return render_ir({"bands": []})
    pts = sorted(((float(wn), float(T)) for wn, T in curve), key=lambda p: -p[0])
    try:
        from digitize_exam import render_ir_tikz, two_scale_tick_xf
        from exam_ir_templates import wn_to_xf

        exam = []
        last = None
        for wn, T in pts:
            if last is not None and abs(last - wn) < step_wn:
                continue
            exam.append([wn, max(2.0, min(98.0, T)), wn_to_xf(wn)])
            last = wn
        return render_ir_tikz(exam, ticks=two_scale_tick_xf())
    except Exception:
        pass
    coords = " ".join(f"({wn:.0f},{max(2.0, min(98.0, T)):.1f})" for wn, T in pts[:: max(1, len(pts)//120)])
    return (
        r"\begin{tikzpicture}[x=-0.00205cm,y=0.048cm,font=\sffamily\small,line cap=round,line join=round]"
        r"\draw (4000,0)--(4000,100)--(400,100)--(400,0)--cycle;"
        r"\foreach \x/\t in {4000/4000,3000/3000,2000/2000,1500/1500,1000/1000,500/500}"
        r"{\draw (\x,0)--++(0,-2.2) node[below]{\t};}"
        r"\foreach \y/\t in {0/0,50/50,100/100}{\draw (4000,\y)--++(-45,0) node[left]{\t};}"
        r"\node[align=center] at (4680,50){transmittance\\/ \%};"
        r"\node at (2200,-14){wavenumber / cm$^{-1}$};"
        r"\draw[thick] plot coordinates {" + coords + r"};"
        r"\end{tikzpicture}"
    )


def render_ir(ir: dict, step: int = 40) -> str:
    """Transmittance vs reverse wavenumber. Bands as Gaussian dips."""
    bands = ir.get("bands") or []
    xs = list(range(400, 4001, step))
    pts = []
    for x in xs:
        t = 92.0
        for b in bands:
            c, w, d = b["center"], max(8, b["width"]), b["depth"]
            shape = b.get("shape") or "sharp"
            # very_broad uses a flatter Gaussian
            sigma = w / (1.2 if shape == "very_broad" else 2.2 if shape == "broad" else 3.0)
            t -= d * math.exp(-0.5 * ((x - c) / sigma) ** 2)
        t = max(8.0, min(96.0, t))
        pts.append(f"({x:.0f},{t:.1f})")
    coords = " ".join(pts)
    return (
        r"\begin{tikzpicture}[x=-0.00205cm,y=0.048cm,font=\sffamily\small,line cap=round,line join=round]"
        r"\draw (4000,0)--(4000,100)--(400,100)--(400,0)--cycle;"
        r"\foreach \x/\t in {4000/4000,3000/3000,2000/2000,1500/1500,1000/1000,500/500}"
        r"{\draw (\x,0)--++(0,-2.2) node[below]{\t};}"
        r"\foreach \y/\t in {0/0,50/50,100/100}{\draw (4000,\y)--++(-45,0) node[left]{\t};}"
        r"\node[align=center] at (4680,50){transmittance\\/ \%};"
        r"\node at (2200,-14){wavenumber / cm$^{-1}$};"
        r"\draw[thick] plot[smooth] coordinates {" + coords + r"};"
        r"\end{tikzpicture}"
    )


def render_ms(ms: dict) -> str:
    peaks = ms.get("peaks") or []
    if not peaks:
        return r"\begin{tikzpicture}\node{no MS}; \end{tikzpicture}"
    xmax = max(p["mz"] for p in peaks) + 5
    xmin = max(0, min(p["mz"] for p in peaks) - 5)
    lines = [
        rf"\begin{{tikzpicture}}[x=0.18cm,y=0.04cm,font=\sffamily\small]",
        rf"\draw ({xmin},0)--({xmax},0)--({xmax},100)--({xmin},100)--cycle;",
    ]
    # x ticks every 10 or at peaks
    step = 10 if xmax - xmin > 30 else 5
    xt = list(range(int(xmin // step * step), int(xmax) + 1, step))
    for x in xt:
        lines.append(rf"\draw ({x},0)--++(0,-3) node[below]{{\footnotesize {x}}};")
    for y in (0, 50, 100):
        lines.append(rf"\draw ({xmin},{y})--++(-1.2,0) node[left]{{\footnotesize {y}}};")
    lines.append(rf"\node[rotate=90] at ({xmin-8},50){{relative intensity}};")
    lines.append(rf"\node at ({(xmin+xmax)/2},-12){{$m/z$}};")
    for p in peaks:
        h = max(2, p["intensity"])
        lines.append(rf"\draw[line width=1.1pt] ({p['mz']},0)--({p['mz']},{h});")
    lines.append(r"\end{tikzpicture}")
    return "".join(lines)


def _multiplet_offsets(mult: str) -> list[tuple[float, float]]:
    """(delta offset ppm, relative height). Exam grain only."""
    m = (mult or "s").lower()
    if m in {"s", "singlet"}:
        return [(0.0, 1.0)]
    if m in {"d", "doublet"}:
        return [(-0.06, 1.0), (0.06, 1.0)]
    if m in {"t", "triplet"}:
        return [(-0.08, 0.5), (0.0, 1.0), (0.08, 0.5)]
    if m in {"q", "quartet"}:
        return [(-0.12, 0.35), (-0.04, 1.0), (0.04, 1.0), (0.12, 0.35)]
    if m in {"sept", "septet"}:
        return [(-0.18, 0.2), (-0.09, 0.6), (0.0, 1.0), (0.09, 0.6), (0.18, 0.2)]
    return [(-0.1, 0.5), (0.0, 0.8), (0.1, 0.5)]  # multiplet blob


def render_hnmr(nmr: dict) -> str:
    peaks = nmr.get("peaks") or []
    lines = [
        r"\begin{tikzpicture}[x=1.1cm,y=0.045cm,font=\sffamily\small]",
        r"\draw (0,0)--(12,0)--(12,100)--(0,100)--cycle;",
    ]
    for x in range(0, 13):
        lines.append(rf"\draw ({x},0)--++(0,-3) node[below]{{\footnotesize {12-x}}};")
    lines.append(r"\node at (6,-12){$\delta$ / ppm};")
    # x=0 is 12 ppm (reverse)
    for p in peaks:
        h = min(95, 18 * p.get("H", 1))
        for off, rel in _multiplet_offsets(p.get("mult") or "s"):
            delta = p["delta"] + off
            x = 12 - delta
            if not (0 <= x <= 12):
                continue
            lines.append(rf"\draw[line width=0.9pt] ({x:.3f},0)--({x:.3f},{h*rel:.1f});")
    lines.append(r"\end{tikzpicture}")
    return "".join(lines)


def render_cnmr(nmr: dict) -> str:
    peaks = nmr.get("peaks") or []
    lines = [
        r"\begin{tikzpicture}[x=0.055cm,y=0.04cm,font=\sffamily\small]",
        r"\draw (0,0)--(220,0)--(220,100)--(0,100)--cycle;",
    ]
    for x in (0, 50, 100, 150, 200):
        lines.append(rf"\draw ({x},0)--++(0,-3) node[below]{{\footnotesize {220-x}}};")
    lines.append(r"\node at (110,-12){$\delta$ / ppm};")
    for p in peaks:
        delta = p["delta"]
        x = 220 - delta
        lines.append(rf"\draw[line width=1.1pt] ({x:.1f},0)--({x:.1f},80);")
    lines.append(r"\end{tikzpicture}")
    return "".join(lines)
