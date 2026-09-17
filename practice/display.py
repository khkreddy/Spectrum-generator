"""Learner-facing stem/options for the practice apps. Does not rewrite freeze."""
from __future__ import annotations

import re

GRAPH = re.compile(
    r"\[(?:Graph|Infra-red|Infrared|The graph)[^\]]*\]",
    re.I,
)
IR_TABLE = re.compile(
    r"(?is)(?:Table:\s*)?bond\s*\|\s*functional groups.*?(?=\n(?:What |Which )|$)"
)
LEAD_NUM = re.compile(r"^\s*(\d{1,2})(?:[.)])?(?:\s+|$)")
UID_Q = re.compile(r":q(\d+)$", re.I)
INLINE_ABCD = re.compile(
    r"(?:^|\n)\s*A\s+.+\s+B\s+.+\s+C\s+.+\s+D\s+\S[\s\S]*$",
    re.I,
)
OPT_LINE = re.compile(r"^\s*([A-D])(?:[.)]\s+|\s+)(\S.*)$")
FIGURE_OPT = re.compile(
    r"^(?:infrared\s+)?spectrum\s+[A-D]\b",
    re.I,
)
LETTER_PREFIX = re.compile(r"^[A-D][.)]\s+")


def qnum(uid: str) -> int | None:
    m = UID_Q.search(uid or "")
    return int(m.group(1)) if m else None


def strip_qnum(stem: str, uid: str) -> str:
    n = qnum(uid)
    if n is None:
        return stem
    lines = (stem or "").splitlines()
    if not lines:
        return stem
    m = LEAD_NUM.match(lines[0])
    if m and int(m.group(1)) == n:
        lines[0] = lines[0][m.end() :].lstrip()
        if not lines[0]:
            lines = lines[1:]
    return "\n".join(lines)


def strip_inline_options(stem: str, options: dict[str, str]) -> str:
    s = stem or ""
    m = INLINE_ABCD.search(s)
    if m:
        s = s[: m.start()].rstrip()
    kept = []
    for ln in s.splitlines():
        om = OPT_LINE.match(ln)
        if om:
            letter, rest = om.group(1), om.group(2).strip()
            opt = str((options or {}).get(letter) or "").strip()
            if opt and (rest == opt or rest.startswith(opt[:24]) or opt.startswith(rest[:24])):
                continue
            if FIGURE_OPT.match(rest):
                continue
        kept.append(ln)
    return "\n".join(kept).rstrip()


def strip_ir_table(stem: str) -> str:
    return IR_TABLE.sub("", stem or "")


def learner_stem(stem: str, options: dict[str, str], uid: str, has_figure: bool) -> str:
    """Original exam wording for display.

    Keeps data-booklet tables (they are part of the printed stem). Strips only
    the leading question number, [Graph: …] placeholders (the PNG is shown),
    and a duplicated A–D dump when options are rendered as buttons.
    `has_figure` is accepted for call-site compatibility; it does not drop tables.
    """
    del has_figure
    s = strip_qnum(stem or "", uid)
    s = GRAPH.sub("", s)
    s = strip_inline_options(s, options or {})
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    s = re.sub(r"[ \t]+\n", "\n", s)
    return s


def technique(spectrum_types: list[str] | None) -> str:
    types = [t.lower() for t in (spectrum_types or []) if t]
    if len(types) > 1:
        return "mixed"
    if types:
        return types[0]
    return "other"


FIGURE_FORMS = {"spectrum_plot", "question_image_with_plot", "other_figure"}


def options_are_figure(options: dict[str, str]) -> bool:
    texts = [str(options.get(k) or "").strip() for k in ("A", "B", "C", "D")]
    nonempty = [t for t in texts if t]
    if len(nonempty) < 4:
        return False
    return all(FIGURE_OPT.match(t) for t in nonempty)


def presentation(
    *,
    visual_form: str | None,
    is_spectrum_plot: bool,
    original_kind: str | None,
    options: dict[str, str],
    has_png: bool,
) -> dict:
    """How to put an item on screen without duplicating the printed paper.

    Base64/PNG is a *figure* (spectrum or option diagrams). A scan of a fully
    encoded text question is not shown. When the PNG is the printed question
    (stem + plot + A–D), the image is the prompt; letters are the selectors.
    """
    fig_opts = options_are_figure(options)
    form = (visual_form or "").strip()
    kind = (original_kind or "").strip()
    encoded_opts = all(str((options or {}).get(k) or "").strip() for k in ("A", "B", "C", "D")) and not fig_opts
    text_scan = form == "text_only" or (
        form == "spectral_table" and not is_spectrum_plot and kind not in {"question_clip", "pdf_page"}
    )
    show_figure = bool(has_png) and not text_scan and (
        fig_opts
        or bool(is_spectrum_plot)
        or form in FIGURE_FORMS
        or kind in {"question_clip", "pdf_page"}
    )
    prompt_in_figure = show_figure
    letter_select = bool(fig_opts or prompt_in_figure)
    return {
        "show_figure": show_figure,
        "prompt_in_figure": prompt_in_figure,
        "letter_select": letter_select,
        "show_stem": not prompt_in_figure,
        "show_option_text": encoded_opts and not prompt_in_figure,
    }


def learner_options(options: dict[str, str]) -> dict[str, str]:
    out = {}
    figure = options_are_figure(options)
    for k in ("A", "B", "C", "D"):
        raw = str((options or {}).get(k) or "").strip()
        if figure:
            out[k] = ""
            continue
        if raw.startswith(k + " ") or LETTER_PREFIX.match(raw):
            raw = LETTER_PREFIX.sub("", raw)
            if raw.startswith(k + " "):
                raw = raw[2:].lstrip()
        out[k] = raw
    return out
