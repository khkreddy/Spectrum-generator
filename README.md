# Spectrum generator

Aliphatic acyclic IR generator plus a 9701 practice pair (student / teacher).

Exam-paper TikZ still sets the **visual grain**. Experimental SDBS liquid-film spectra supply **diagnostic peak positions, shapes and ranges** the papers simplified away.

## Propan-1-ol vs propan-2-ol

The generator does not look up a stored trace per name. RDKit flags pick a class template:

| molecule | SMILES | SMARTS | template |
|---|---|---|---|
| propan-1-ol | `CCCO` | `[CH2][OX2H]` | `primary_alcohol` |
| propan-2-ol | `CC(C)O` | `[CH1]([#6])[OX2H]` and not primary | `secondary_alcohol` |

Diagnostic overlay from the experimental aliphatic corpus:

| band | 1° alcohol | 2° alcohol |
|---|---|---|
| O–H | 3200–3550, broad | 3200–3550, broad |
| CH₂ scissor | **1440–1475**, rounded (exam gold of 9701_s18_qp_11:q30 sat at T≈83 / baseline; Luna 1-propanol T(1465)≈26) | present |
| CH₃ bend / isopropyl | 1360–1390, moderate | **1360–1390, strong** |
| C–O | **1000–1085** (1°) | **1085–1160** (2°; exam gold sat at baseline near 1130; overlay restores T≈9) |

So a generated propan-1-ol now shows the ~1450 cm⁻¹ CH₂ band. Propan-2-ol is the other template: deeper ~1375 cm⁻¹ isopropyl and 2° C–O ~1130 cm⁻¹, without a 1° C–O near 1050 cm⁻¹.

## Experimental peak catalog

`src/extract_aliphatic_experimental.py` walks every aliphatic acyclic system in the SDBS inventory (aromatics and rings excluded).

- Preferred source: Luna TikZ encodings of the liquid-film GIFs (trough, FWHM, shape).
- Otherwise: digitised `curve_ds` with the same trough finder.
- GIF **minima lists are not used** — they mark the 3850 cm⁻¹ y-axis as O–H.

Output: `data/rules/aliphatic_experimental_peaks.json` (235 molecules, 20 families, overlay bands the exam envelope omitted).

## Practice apps

Student and teacher papers render the **original exam crop as base64**, not a TikZ redraw of the question.

- Student: A–D are highlighted once in the selection row. They are **not** repeated in the stem. Figure-only options (four plotted spectra) are letter buttons only.
- Wrong A–D opens a **precomputed learn-by-solve follow-up** for that option’s V2 mx pathway (`term_substitution`, `condition_omission`, `relationship_reversal`, `scope_error`, `surface_feature_capture`, `mechanism_conflation`, `operation_confusion`). Runtime is a JSON lookup. The mx type is **not** shown to the student.
- Teacher PDF = question paper + attached answer key (hinge solve, mx pathway per wrong option, follow-up item and its key).

43 MCQs × 3 wrong options = 129 follow-ups in `practice/static/lbs.json`.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python src/cli.py 'CCCO' 'propan-1-ol'
PYTHONPATH=src .venv/bin/python practice/server.py
# http://127.0.0.1:8778/
```

Generator is aliphatic **acyclic** only (no rings, no aromatics).

## GitHub Pages

`docs/` is the static student / teacher / example-generator site. Arbitrary SMILES still need the Python server.
