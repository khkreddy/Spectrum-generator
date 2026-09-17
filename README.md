# 9701 spectroscopy

Cambridge International AS & A Level Chemistry **Paper 1 MCQs** on infrared, mass spectrometry, and combined techniques, plus an aliphatic IR generator.

The question a student or teacher sees is the **original exam wording** (including the printed data-booklet table) and the **original figure** (PNG stored as base64). A–D are selectable buttons. That is the paper, not a TikZ impersonation of the paper.

## Practice

| | |
|---|---|
| Student | Filter IR / MS / combined / mixed set. Answer A–D. A wrong letter opens a smaller follow-up aimed at that mistake. |
| Teacher | The same filters. Print the paper as students see it. The key attaches hinge solve, misconception pathway, follow-up. |
| Generator | Open-chain aliphatic SMILES → exam-class IR. |

NMR items in this harvest are paper-4 structured responses, not A–D, so the NMR filter is empty on purpose.

Learn-by-solve records are authored **offline**. The Astra harness (`src/ask_astra_lbs.py`) writes schema-checked JSON; the browser looks that JSON up. Runtime does not call a model. Misconception types stay on the teacher key.

Mark-scheme letters come from the published Paper 1 PDFs (`practice/extract_ms_keys.py`), cross-checked against the TTwin keys already on disk. Items without a key are not served.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python src/cli.py 'CCCO' 'propan-1-ol'
PYTHONPATH=src .venv/bin/python practice/server.py
# http://127.0.0.1:8778/
```

Rebuild the MCQ pack (needs the harvest tree and mark-scheme PDFs):

```bash
PYTHONPATH=src .venv/bin/python practice/extract_ms_keys.py
PYTHONPATH=src .venv/bin/python practice/build_pack.py
PYTHONPATH=src .venv/bin/python practice/test_practice.py
```

Author follow-ups for any new keyed MCQ:

```bash
PYTHONPATH=src .venv/bin/python src/ask_astra_lbs.py --missing
```

## GitHub Pages

`docs/` is the static student / teacher / example-generator site. Arbitrary SMILES still need the Python server.

Generator is aliphatic **acyclic** only (no rings, no aromatics).
