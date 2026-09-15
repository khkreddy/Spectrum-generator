"""Digitize printed 9701 IR/MS diagrams from harvest PNGs.

IR: detect the axis rectangle, map ticks (Cambridge two-scale 4000–2000 / 2000–500),
trace the transmittance polyline. Native TikZ is rendered separately.

Does not rewrite freeze exam.v1.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TICK_SETS = {
    8: [4000.0, 3500.0, 3000.0, 2500.0, 2000.0, 1500.0, 1000.0, 500.0],
    7: [4000.0, 3000.0, 2500.0, 2000.0, 1500.0, 1000.0, 500.0],
    6: [4000.0, 3000.0, 2000.0, 1500.0, 1000.0, 500.0],
    5: [4000.0, 3000.0, 2000.0, 1000.0, 500.0],
}


def _longest_run(row: np.ndarray, gap: int = 2) -> tuple[int, int, int]:
    """Longest True run, allowing `gap` False pixels so anti-aliased frames still match."""
    best = cur = 0
    b0 = b1 = 0
    start = None
    miss = 0
    for i, v in enumerate(row):
        if v:
            if start is None:
                start = i
            cur = i - start + 1
            miss = 0
            if cur > best:
                best, b0, b1 = cur, start, i
        elif start is not None and miss < gap:
            miss += 1
        else:
            cur = 0
            start = None
            miss = 0
    return best, b0, b1


def _dilate(mask: np.ndarray, k: int = 1) -> np.ndarray:
    out = mask.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            if dy == 0 and dx == 0:
                continue
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def _all_runs(row: np.ndarray, min_w: int, gap: int = 2) -> list[tuple[int, int, int]]:
    """Every True-run longer than min_w (gap-tolerant)."""
    runs: list[tuple[int, int, int]] = []
    start = None
    miss = 0
    last_true = 0
    for i, v in enumerate(row):
        if v:
            if start is None:
                start = i
            last_true = i
            miss = 0
        elif start is not None and miss < gap:
            miss += 1
        else:
            if start is not None and last_true - start + 1 >= min_w:
                runs.append((last_true - start + 1, start, last_true))
            start = None
            miss = 0
    if start is not None and last_true - start + 1 >= min_w:
        runs.append((last_true - start + 1, start, last_true))
    return runs


def _cluster_hlines(dark: np.ndarray, min_w: int) -> list[dict]:
    h, _w = dark.shape
    raw = []
    for y in range(h):
        for ln, x0, x1 in _all_runs(dark[y], min_w, gap=2):
            raw.append((y, x0, x1, ln))
    clusters: list[dict] = []
    for y, x0, x1, ln in raw:
        placed = False
        for c in reversed(clusters[-6:]):
            if y - c["ys"][-1] <= 3 and abs(c["x0"] - x0) < 18 and abs(c["x1"] - x1) < 18:
                c["ys"].append(y)
                c["x0"] = min(c["x0"], x0)
                c["x1"] = max(c["x1"], x1)
                c["ln"] = max(c["ln"], ln)
                placed = True
                break
        if not placed:
            clusters.append({"ys": [y], "x0": x0, "x1": x1, "ln": ln})
    return [
        {"y": int(np.median(c["ys"])), "x0": c["x0"], "x1": c["x1"], "ln": c["ln"]}
        for c in clusters
    ]


def _is_table(gray: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> bool:
    """True when the rectangle is a ruled table, not a spectrum frame."""
    interior = gray[y0 + 4 : y1 - 4, x0 + 4 : x1 - 4]
    if interior.size == 0:
        return False
    dark = interior < 110
    min_w = int(0.40 * dark.shape[1])
    hcount = 0
    last = -99
    for y in range(dark.shape[0]):
        ln, _, _ = _longest_run(dark[y], gap=2)
        if ln >= min_w and y - last > 6:
            hcount += 1
            last = y
    min_h = int(0.40 * dark.shape[0])
    vcount = 0
    last = -99
    for x in range(dark.shape[1]):
        ln, _, _ = _longest_run(dark[:, x], gap=2)
        if ln >= min_h and x - last > 6:
            vcount += 1
            last = x
    return hcount >= 3 or (hcount >= 2 and vcount >= 2)


def find_plot_boxes(gray: np.ndarray) -> list[dict]:
    """Axis rectangles that look like IR/MS plot frames, not tables."""
    h, w = gray.shape
    found: list[dict] = []
    for thr, dil in ((80, 0), (100, 0), (120, 1), (70, 1)):
        dark = gray < thr
        if dil:
            dark = _dilate(dark, dil)
        lines = _cluster_hlines(dark, min_w=max(140, int(0.14 * w)))
        for i, a in enumerate(lines):
            for b in lines[i + 1 :]:
                if abs(a["x0"] - b["x0"]) > 14 or abs(a["x1"] - b["x1"]) > 14:
                    continue
                y0, y1 = a["y"], b["y"]
                x0 = min(a["x0"], b["x0"])
                x1 = max(a["x1"], b["x1"])
                height = y1 - y0
                width = x1 - x0
                if height < 60 or width < 150:
                    continue
                ar = width / height
                if ar < 1.05 or ar > 3.05:
                    continue
                internal = 0
                for m in lines:
                    if y0 + 8 < m["y"] < y1 - 8 and abs(m["x0"] - x0) < 16 and abs(m["x1"] - x1) < 16:
                        internal += 1
                if internal >= 2:
                    continue
                interior = dark[y0 + 4 : y1 - 4, x0 + 4 : x1 - 4]
                if interior.size == 0:
                    continue
                frac = float(interior.mean())
                if frac < 0.003 or frac > 0.15:
                    continue
                if _is_table(gray, x0, y0, x1, y1):
                    continue
                found.append(
                    {
                        "x0": int(x0),
                        "y0": int(y0),
                        "x1": int(x1),
                        "y1": int(y1),
                        "ar": ar,
                        "frac": frac,
                    }
                )
    # non-max suppression
    found.sort(key=lambda b: (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]), reverse=True)
    kept: list[dict] = []
    for b in found:
        area = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
        hit = False
        for k in kept:
            ox = max(0, min(b["x1"], k["x1"]) - max(b["x0"], k["x0"]))
            oy = max(0, min(b["y1"], k["y1"]) - max(b["y0"], k["y0"]))
            if ox * oy > 0.28 * area:
                hit = True
                break
        if not hit:
            kept.append(b)
    kept.sort(key=lambda b: (b["y0"], b["x0"]))
    return kept


def detect_xticks(gray: np.ndarray, box: dict) -> list[float]:
    """Pixel x of tick marks in a thin band just below the axis (not the numerals)."""
    x0, y1, x1 = box["x0"], box["y1"], box["x1"]
    h, w = gray.shape
    y_a = min(h - 1, y1 + 2)
    y_b = min(h, y1 + 14)
    if y_b - y_a < 5:
        return []
    band = gray[y_a:y_b, max(0, x0) : min(w, x1)]
    dark = band < 90
    col = dark.sum(axis=0)
    xs = np.where(col >= 2)[0]
    clusters: list[list[int]] = []
    for x in xs:
        if clusters and x - clusters[-1][-1] <= 3:
            clusters[-1].append(int(x))
        else:
            clusters.append([int(x)])
    width = max(1, x1 - x0)
    ticks = [float(x0 + np.mean(c)) for c in clusters if 1 <= len(c) <= 6]
    # min spacing ~6% of axis so label ink does not become extra ticks
    filtered: list[float] = []
    for t in ticks:
        if not filtered or (t - filtered[-1]) > 0.055 * width:
            filtered.append(t)
    if not (4 <= len(filtered) <= 8):
        return []
    return filtered


def wn_mapper(box: dict, ticks: list[float]):
    """Pixel x → wavenumber using detected ticks or Cambridge two-scale fallback."""
    x0, x1 = float(box["x0"]), float(box["x1"])
    n = len(ticks)
    labels = TICK_SETS.get(n)
    if labels and ticks[0] < ticks[-1]:
        tx = np.array(ticks, dtype=float)
        wn = np.array(labels, dtype=float)

        def map_x(x: float) -> float:
            return float(np.interp(x, tx, wn))

        return map_x, list(zip(ticks, labels))
    # two-scale fallback: 4000–2000 on left ~40%, 2000–500 on the rest
    mid = x0 + 0.40 * (x1 - x0)

    def map_x(x: float) -> float:
        if x <= mid:
            t = (x - x0) / max(1.0, mid - x0)
            return 4000.0 - t * 2000.0
        t = (x - mid) / max(1.0, x1 - mid)
        return 2000.0 - t * 1500.0

    return map_x, [(x0, 4000.0), (mid, 2000.0), (x1, 500.0)]


def two_scale_tick_xf() -> list[tuple[float, float]]:
    """Cambridge IR: 4000–2000 on left ~40%, 2000–500 stretched on the rest."""
    return [
        (0.00, 4000.0),
        (0.20, 3000.0),
        (0.40, 2000.0),
        (0.60, 1500.0),
        (0.80, 1000.0),
        (1.00, 500.0),
    ]


def tick_xf_list(box: dict, ticks: list[float]) -> list[tuple[float, float]]:
    x0, x1 = float(box["x0"]), float(box["x1"])
    width = max(1.0, x1 - x0)
    n = len(ticks)
    labels = TICK_SETS.get(n)
    if labels and ticks[0] < ticks[-1]:
        return [((t - x0) / width, lab) for t, lab in zip(ticks, labels)]
    return two_scale_tick_xf()


def trace_ir_curve(gray: np.ndarray, box: dict) -> tuple[list[tuple[float, float, float]], list[tuple[float, float]]]:
    """Return ([(wn, T, xf), ...], tick_xf). xf=0 at the left axis (4000).

    Transmittance is the first dark stroke from the TOP of the frame, so the
    left y-axis (full-height ink) is skipped instead of becoming a fake peak.
    """
    ticks = detect_xticks(gray, box)
    map_x, _cal = wn_mapper(box, ticks)
    tick_xf = tick_xf_list(box, ticks)
    inset = max(5, int(0.012 * (box["x1"] - box["x0"])))
    x0 = box["x0"] + inset
    x1 = box["x1"] - inset
    y0 = box["y0"] + 3
    y1 = box["y1"] - 3
    height = max(1, y1 - y0)
    span_w = max(1, box["x1"] - box["x0"])
    pts: list[tuple[float, float, float]] = []
    for x in range(x0, x1 + 1):
        col = gray[y0 : y1 + 1, x]
        dark_i = np.where(col < 110)[0]
        if dark_i.size == 0:
            continue
        span = int(dark_i[-1] - dark_i[0])
        # full-height ink = axis, not the curve
        if span > 0.22 * height and dark_i[0] <= 3:
            continue
        # first contiguous dark run from the top = the transmittance line
        run0 = int(dark_i[0])
        run1 = run0
        for k in dark_i[1:]:
            if int(k) <= run1 + 2:
                run1 = int(k)
            else:
                break
        yi = y0 + (run0 + run1) / 2.0
        if yi <= y0 + 1.5:
            continue
        xf = (x - box["x0"]) / span_w
        if xf < 0.012:
            continue
        wn = map_x(float(x))
        T = 100.0 * (1.0 - (yi - y0) / height)
        T = max(0.0, min(100.0, T))
        pts.append((wn, T, xf))
    pts = _strip_left_plunge(pts)
    return pts, tick_xf


def _strip_left_plunge(pts: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Drop y-axis ink that reads as a rising lead-in at xf≈0 (fake peak at 4000)."""
    if len(pts) < 16:
        return pts
    left = [p for p in pts if p[2] < 0.08]
    if left:
        t_max = max(p[1] for p in left)
        i = 0
        while i < len(pts) and pts[i][2] < 0.08 and pts[i][1] < t_max - 10:
            i += 1
        pts = pts[i:] or pts
    # second pass: compare the far-left to the nearby baseline (xf 0.10–0.22)
    hi = [p[1] for p in pts if 0.10 <= p[2] <= 0.22]
    if hi:
        t_hi = max(hi)
        i = 0
        while i < len(pts) and pts[i][2] < 0.12 and pts[i][1] < t_hi - 15:
            i += 1
        pts = pts[i:] or pts
    return pts


def downsample_curve(pts: list[tuple[float, float, float]], n: int = 180) -> list[tuple[float, float, float]]:
    """Keep trough neighborhoods (rounded bottoms) plus a regular sample."""
    if len(pts) <= n:
        return pts
    keep = {0, len(pts) - 1}
    for i in range(1, len(pts) - 1):
        t0, t1, t2 = pts[i - 1][1], pts[i][1], pts[i + 1][1]
        if t1 <= t0 and t1 <= t2:
            # window around the trough so a U stays rounded, not a V
            lo = max(0, i - 6)
            hi = min(len(pts) - 1, i + 6)
            for j in range(lo, hi + 1):
                if pts[j][1] <= t1 + 10:
                    keep.add(j)
        if t1 >= t0 and t1 >= t2 and t1 > 70:
            keep.add(i)
        if t1 < 45:
            keep.add(i)
    step = max(1, len(pts) // n)
    for i in range(0, len(pts), step):
        keep.add(i)
    return [pts[i] for i in sorted(keep)]


def digitize_ir(path: Path) -> list[dict]:
    gray = np.array(Image.open(path).convert("L"))
    boxes = find_plot_boxes(gray)
    panels = []
    for i, box in enumerate(boxes):
        raw, tick_xf = trace_ir_curve(gray, box)
        curve = downsample_curve(raw, 180)
        if len(curve) < 20:
            continue
        if min(t for _w, t, _x in curve) > 55:
            continue
        if not (1.15 <= box["ar"] <= 2.95):
            continue
        deep = sorted(curve, key=lambda p: p[1])[:8]
        panels.append(
            {
                "panel": i,
                "box": box,
                "n_raw": len(raw),
                "curve": [[round(w, 1), round(t, 1), round(xf, 4)] for w, t, xf in curve],
                "ticks": [[round(xf, 4), int(wn)] for xf, wn in tick_xf],
                "minima": [[round(w, 0), round(t, 1)] for w, t, _x in deep],
                "T4000": round(curve[0][1], 1),
                "T500": round(curve[-1][1], 1),
            }
        )
    return panels


def overlay_debug(path: Path, dest: Path, panels: list[dict]) -> None:
    rgb = Image.open(path).convert("RGB")
    dr = ImageDraw.Draw(rgb)
    colors = [(220, 0, 0), (0, 80, 220), (0, 150, 40), (200, 120, 0)]
    gray = np.array(Image.open(path).convert("L"))
    for i, pan in enumerate(panels):
        b = pan["box"]
        col = colors[i % 4]
        dr.rectangle([b["x0"], b["y0"], b["x1"], b["y1"]], outline=col, width=3)
        raw, _ticks = trace_ir_curve(gray, b)
        span_w = max(1, b["x1"] - b["x0"])
        y0 = b["y0"] + 3
        y1 = b["y1"] - 3
        height = max(1, y1 - y0)
        pts_xy = []
        for _wn, T, xf in raw:
            x = int(round(b["x0"] + xf * span_w))
            yi = int(round(y0 + (1 - T / 100.0) * height))
            pts_xy.append((x, yi))
        for j in range(1, len(pts_xy)):
            dr.line([pts_xy[j - 1], pts_xy[j]], fill=col, width=2)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(dest)


def render_ir_tikz(curve: list, ticks: list | None = None, label: str | None = None) -> str:
    """Native TikZ on the paper's warped x-scale. xf=0 is 4000 (left)."""
    W = 10.0
    pts = []
    for row in curve:
        if len(row) >= 3:
            _wn, T, xf = float(row[0]), float(row[1]), float(row[2])
        else:
            wn, T = float(row[0]), float(row[1])
            # fallback linear 4000→500
            xf = (4000.0 - wn) / 3500.0
        pts.append((max(0.0, min(W, xf * W)), max(0.0, min(100.0, T))))
    if not pts:
        return ""
    coords = " ".join(f"({x:.3f},{t:.1f})" for x, t in pts)
    tick_pairs = ticks or two_scale_tick_xf()
    tick_s = ",".join(f"{float(xf) * W:.2f}/{int(wn)}" for xf, wn in tick_pairs)
    title = rf"\node at ({W/2:.1f},112){{{label}}};" if label else ""
    return (
        rf"\begin{{tikzpicture}}[x=1cm,y=0.048cm,font=\sffamily\small,"
        r"line cap=round,line join=round]"
        "\n"
        rf"\draw (0,0)--(0,100)--({W:.1f},100)--({W:.1f},0)--cycle;"
        "\n"
        rf"\foreach \x/\t in {{{tick_s}}}"
        r"{\draw (\x,0)--++(0,-0.18cm) node[below]{\t};}"
        "\n"
        r"\foreach \y/\t in {0/0,50/50,100/100}"
        r"{\draw (0,\y)--++(-0.42cm,0) node[left]{\t};}"
        "\n"
        r"\node[align=center,anchor=east] at (-0.55,50){transmittance\\/ \%};"
        "\n"
        rf"\node at ({W/2:.1f},-16){{wavenumber / cm$^{{-1}}$}};"
        "\n"
        + title
        + r"\draw[thick] plot coordinates {"
        + coords
        + r"};"
        "\n"
        r"\end{tikzpicture}"
        "\n"
    )


def render_ms_tikz(
    peaks: list[dict],
    *,
    xmin: float,
    xmax: float,
    ymax: float,
    xlabel: str = "m/e",
    ylabel: str = "abundance",
    label: str | None = None,
    y_numbers: bool | None = None,
) -> str:
    """L-shaped exam MS. TikZJax-safe: no footnotesize/textbf/mixed-unit ticks."""
    mzs = [float(p["mz"]) for p in peaks] or [0.0]
    tick_lo = int(round(float(xmin)))
    tick_hi = int(round(float(xmax)))
    if tick_hi <= tick_lo:
        tick_hi = tick_lo + 5
    # origin sits left of the first labelled tick if a stick is on that tick
    axis_x0 = float(tick_lo) - (0.55 if any(abs(mz - tick_lo) < 0.2 for mz in mzs) else 0.0)
    axis_x1 = float(tick_hi)
    ytop = float(ymax) if ymax > 0 else 100.0
    if y_numbers is None:
        y_numbers = ytop <= 70 or any("." in str(p.get("label") or "") for p in peaks)
    xspan = max(4.0, axis_x1 - axis_x0)
    xunit = min(1.15, 11.0 / xspan)
    yunit = 0.048
    y_axis = max(ytop, 100.0) if not y_numbers else ytop
    headroom = y_axis * 1.18
    lines = [
        rf"\begin{{tikzpicture}}[x={xunit:.3f}cm,y={yunit:.3f}cm,font=\sffamily\small,line cap=round]",
        rf"\draw ({axis_x0:.2f},0)--({axis_x1:.2f},0);",
        rf"\draw ({axis_x0:.2f},0)--({axis_x0:.2f},{y_axis:.0f});",
    ]
    if label:
        lines.append(rf"\node at ({(axis_x0+axis_x1)/2:.2f},{headroom:.0f}){{{label}}};")
    step = 1 if (tick_hi - tick_lo) <= 16 else (2 if (tick_hi - tick_lo) <= 40 else 10)
    for x in range(tick_lo, tick_hi + 1, step):
        lines.append(rf"\draw ({x},0)--({x},-4) node[below]{{{x}}};")
    if y_numbers:
        for y in (0, int(y_axis / 2), int(y_axis)):
            lines.append(rf"\draw ({axis_x0:.2f},{y})--({axis_x0 - 0.25:.2f},{y}) node[left]{{{y}}};")
    xlab = xlabel.replace("$", "").replace(r"\ ", " ")
    ylab = ylabel.replace(r"\%", "%").replace("$", "")
    lines.append(rf"\node[rotate=90] at ({axis_x0 - 1.35:.2f},{y_axis/2:.0f}){{{ylab}}};")
    lines.append(rf"\node at ({(axis_x0+axis_x1)/2:.2f},-11){{{xlab}}};")
    for p in peaks:
        mz = float(p["mz"])
        inten = float(p["intensity"])
        lines.append(rf"\draw[line width=1.4pt] ({mz},0)--({mz},{inten});")
        lab = p.get("label")
        if lab not in (None, ""):
            lab_s = str(lab).replace("%", r"\%")
            lines.append(rf"\node[above] at ({mz},{inten}){{{lab_s}}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines) + "\n"


def _nmr_sticks(delta: float, mult: str, height: float) -> list[tuple[float, float]]:
    """Exam-grain multiplet. Quartet is four lines 1:3:3:1, not a 6-line clump."""
    m = (mult or "s").lower()
    j = 0.11  # ~7 Hz on the 11→0 ppm exam axis
    if m in {"s", "singlet"}:
        return [(delta, height)]
    if m in {"d", "doublet"}:
        return [(delta - j / 2, height), (delta + j / 2, height)]
    if m in {"t", "triplet"}:
        return [(delta - j, height * 0.52), (delta, height), (delta + j, height * 0.52)]
    if m in {"q", "quartet"}:
        return [
            (delta - 1.5 * j, height * 0.34),
            (delta - 0.5 * j, height),
            (delta + 0.5 * j, height),
            (delta + 1.5 * j, height * 0.34),
        ]
    return [(delta, height)]


def render_nmr_tikz(
    peaks: list[dict],
    *,
    ppm_left: float = 11.0,
    ppm_right: float = 0.0,
) -> str:
    """9701 1H style: 11 LEFT → 0 RIGHT, baseline strip, peaks standing on the strip."""
    span = abs(ppm_left - ppm_right) or 11.0
    xunit = 1.05
    strip = 7.0
    ymax = 100.0
    lines = [
        rf"\begin{{tikzpicture}}[x={xunit:.3f}cm,y=0.048cm,font=\sffamily\small,line cap=round]",
        rf"\draw (0,{strip})--({span},{strip})--({span},{ymax})--(0,{ymax})--cycle;",
        rf"\draw (0,0)--({span},0)--({span},{strip})--(0,{strip})--cycle;",
    ]
    ntick = int(round(span))
    for i in range(ntick + 1):
        ppm = ppm_left - i * (ppm_left - ppm_right) / ntick
        x = i * span / ntick
        lines.append(rf"\draw ({x:.2f},0)--({x:.2f},-3) node[below]{{{ppm:.0f}}};")
    lines.append(rf"\node at ({span/2},-11){{$\delta$ / ppm}};")
    for p in peaks:
        h = min(92.0, float(p.get("intensity") or 70))
        for delta, hh in _nmr_sticks(float(p["delta"]), str(p.get("mult") or "s"), h):
            x = (ppm_left - delta) / (ppm_left - ppm_right) * span
            if 0 <= x <= span:
                lines.append(rf"\draw[line width=1.2pt] ({x:.3f},{strip})--({x:.3f},{strip + hh:.1f});")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines) + "\n"
