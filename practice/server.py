#!/usr/bin/env python3
"""Aliphatic exam practice + canonical IR generator.

  .venv/bin/python practice/server.py
  http://127.0.0.1:8778/
"""
from __future__ import annotations

import io
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
CANON = ROOT.parent
SRC = CANON / "src"
HARVEST_ITEMS = Path("/home/harik/awm_build/data/spectra/items")
PACK = ROOT / "static" / "pack.json"
LBS_PATH = ROOT / "static" / "lbs.json"
PORT = 8778

sys.path.insert(0, str(SRC))
from generate import generate  # noqa: E402
from names import resolve  # noqa: E402
from render_tikz import render_all  # noqa: E402


def load_pack() -> dict:
    return json.loads(PACK.read_text(encoding="utf-8")) if PACK.is_file() else {"items": []}


def load_lbs() -> dict:
    if not LBS_PATH.is_file():
        return {"items": {}}
    return json.loads(LBS_PATH.read_text(encoding="utf-8"))


PACK_DOC = load_pack()
BY_UID = {it["uid"]: it for it in PACK_DOC.get("items") or []}
LBS_DOC = load_lbs()
LBS = LBS_DOC.get("items") or {}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])
        if path in ("/", ""):
            self.path = "/hub.html"
            return super().do_GET()
        if path.startswith("/media/"):
            return self._file(HARVEST_ITEMS, path[len("/media/") :], ctype="image/png")
        if path == "/api/catalog":
            return self._json(200, self._student_catalog())
        if path == "/api/teacher-catalog":
            return self._json(200, self._teacher_payload())
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid json"})
        if path == "/api/grade":
            return self._grade(body)
        if path == "/api/generate":
            return self._generate(body)
        if path == "/api/pdf":
            return self._pdf(body)
        self.send_error(404)

    def _student_catalog(self) -> dict:
        items = []
        for it in PACK_DOC.get("items") or []:
            if not (it.get("options") and it.get("key")):
                continue
            items.append(
                {
                    "uid": it["uid"],
                    "spectrum_types": it.get("spectrum_types") or [],
                    "stem": it.get("stem") or "",
                    "options": it.get("options") or {},
                    "options_are_figure": bool(it.get("options_are_figure")),
                    "original_base64": it.get("original_base64"),
                    "has_examiner_comment": bool(it.get("examiner_comment")),
                    "has_lbs": bool(it.get("has_lbs")),
                    "aliphatic_class": it.get("aliphatic_class"),
                }
            )
        return {"n": len(items), "items": items}

    def _teacher_payload(self) -> dict:
        items = []
        for it in PACK_DOC.get("items") or []:
            rec = dict(it)
            rec["lbs"] = LBS.get(it["uid"])
            items.append(rec)
        return {**PACK_DOC, "items": items, "lbs_n": len(LBS)}

    def _grade(self, body: dict):
        uid = body.get("uid") or ""
        choice = (body.get("choice") or "").strip().upper()
        stage = (body.get("stage") or "item").strip().lower()
        it = BY_UID.get(uid)
        if not it or not it.get("key"):
            return self._json(404, {"error": "unknown item"})
        lbs = LBS.get(uid) or {}
        if stage == "followup":
            from_choice = (body.get("from_choice") or "").strip().upper()
            row = (lbs.get("wrong") or {}).get(from_choice) or {}
            fu = row.get("followup") or {}
            fkey = fu.get("key")
            if not fkey:
                return self._json(400, {"error": "no follow-up for that option"})
            ok = choice == fkey
            return self._json(
                200,
                {
                    "uid": uid,
                    "stage": "followup",
                    "choice": choice,
                    "ok": ok,
                    "correct": fkey,
                    "why": fu.get("why"),
                    "original_key": it["key"],
                    "solve": lbs.get("solve"),
                    "examiner_comment": it.get("examiner_comment"),
                    "from_choice": from_choice,
                },
            )
        key = it["key"]
        ok = choice == key
        if ok:
            return self._json(
                200,
                {
                    "uid": uid,
                    "stage": "item",
                    "choice": choice,
                    "correct": key,
                    "ok": True,
                    "solve": lbs.get("solve"),
                    "examiner_comment": it.get("examiner_comment"),
                },
            )
        row = (lbs.get("wrong") or {}).get(choice) or {}
        fu = row.get("followup")
        return self._json(
            200,
            {
                "uid": uid,
                "stage": "item",
                "choice": choice,
                "ok": False,
                "followup": fu,
                "from_choice": choice,
            },
        )

    def _generate(self, body: dict):
        molecule = (body.get("molecule") or "").strip()
        if not molecule:
            return self._json(400, {"error": "type a name or SMILES"})
        try:
            resolved = resolve(molecule)
            spec = generate(resolved["smiles"], name=resolved["name"])
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except Exception as e:
            return self._json(400, {"error": str(e)[:300]})
        tikz = render_all(spec)
        ident = spec.get("identifiable") or {}
        return self._json(
            200,
            {
                "name": resolved["name"],
                "smiles": spec["smiles"],
                "formula": spec["formula"],
                "family": (spec.get("ir") or {}).get("family"),
                "aliphatic_acyclic": True,
                "identifiable": ident,
                "tikz": tikz.get("ir"),
                "ms": tikz.get("ms"),
                "hnmr": tikz.get("hnmr"),
                "cnmr": tikz.get("cnmr"),
            },
        )

    def _pdf(self, body: dict):
        uids = body.get("uids") or []
        include_answers = True if "answers" not in body else bool(body.get("answers"))
        items = [BY_UID[u] for u in uids if u in BY_UID]
        if not items:
            return self._json(400, {"error": "no questions selected"})
        try:
            pdf = _render_pdf(items, include_answers=include_answers)
        except Exception as e:
            return self._json(500, {"error": str(e)[:300]})
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", 'attachment; filename="9701-spectra-pack.pdf"')
        self.send_header("Content-Length", str(len(pdf)))
        self.end_headers()
        self.wfile.write(pdf)

    def _file(self, root: Path, rel: str, ctype: str | None = None):
        rel = unquote(rel).lstrip("/")
        if ".." in rel or rel.startswith("/"):
            self.send_error(400)
            return
        fp = root / rel
        if not fp.is_file():
            self.send_error(404)
            return
        data = fp.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _wrap(text: str, width: int = 92) -> str:
    words = (text or "").replace("\n", " ").split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def _render_pdf(items: list[dict], include_answers: bool) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image as PILImage

    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        for it in items:
            fig = plt.figure(figsize=(8.27, 11.69), dpi=120)
            fig.patch.set_facecolor("white")
            fig.text(0.08, 0.96, "9701 spectroscopy  ·  teacher pack", fontsize=9, color="#555")
            fig.text(0.08, 0.93, it["uid"], fontsize=11, fontweight="bold", fontfamily="monospace")
            stem = _wrap(it.get("stem") or "", 95)
            fig.text(0.08, 0.90, stem, fontsize=8.5, va="top", wrap=False, family="DejaVu Sans")
            y = 0.90 - 0.012 * (stem.count("\n") + 2)
            png = HARVEST_ITEMS / it["folder"] / "original.png"
            im = None
            if png.is_file():
                im = PILImage.open(png).convert("RGB")
            elif it.get("original_base64"):
                import base64 as _b64
                blob = it["original_base64"].split(",", 1)[-1]
                im = PILImage.open(io.BytesIO(_b64.b64decode(blob))).convert("RGB")
            if im is not None and y > 0.42:
                ax = fig.add_axes([0.08, 0.34, 0.84, min(0.48, y - 0.38)])
                ax.imshow(im)
                ax.axis("off")
            opts = it.get("options") or {}
            figure_opts = bool(it.get("options_are_figure"))
            oy = 0.30
            for lab in ("A", "B", "C", "D"):
                if lab not in opts and lab not in (it.get("options_raw") or {}):
                    continue
                text = "" if figure_opts else str(opts.get(lab) or "")
                line = lab if not text else f"{lab}  {_wrap(text, 88).split(chr(10))[0][:110]}"
                fig.text(0.08, oy, line, fontsize=9)
                oy -= 0.025
            pdf.savefig(fig)
            plt.close(fig)
        if include_answers:
            fig = plt.figure(figsize=(8.27, 11.69), dpi=120)
            fig.text(0.08, 0.96, "Answer key  ·  learn-by-solve", fontsize=12, fontweight="bold")
            y = 0.93

            def flush():
                nonlocal fig, y
                pdf.savefig(fig)
                plt.close(fig)
                fig = plt.figure(figsize=(8.27, 11.69), dpi=120)
                y = 0.95

            for it in items:
                if y < 0.22:
                    flush()
                key = it.get("key") or "—"
                lbs = LBS.get(it["uid"]) or {}
                fig.text(0.08, y, f"{it['uid']}   {key}", fontsize=9, fontfamily="monospace", fontweight="bold")
                y -= 0.018
                solve = (lbs.get("solve") or "").strip()
                if solve:
                    for ln in _wrap(solve, 96).split("\n")[:8]:
                        fig.text(0.08, y, ln, fontsize=7.5, color="#222")
                        y -= 0.014
                    y -= 0.004
                for lab in ("A", "B", "C", "D"):
                    if lab == key:
                        continue
                    row = (lbs.get("wrong") or {}).get(lab) or {}
                    fu = row.get("followup") or {}
                    if not row:
                        continue
                    if y < 0.16:
                        flush()
                    mx = row.get("mx_type") or ""
                    fig.text(0.08, y, f"If {lab}  [{mx}]", fontsize=7.5, color="#8a3b2b")
                    y -= 0.013
                    path = (row.get("pathway") or "")[:220]
                    if path:
                        fig.text(0.10, y, _wrap(path, 100).split("\n")[0][:120], fontsize=7, color="#444")
                        y -= 0.013
                    fst = (fu.get("stem") or "").replace("\n", " ")[:180]
                    if fst:
                        fig.text(0.10, y, "Follow-up: " + fst, fontsize=7, color="#1f6f64")
                        y -= 0.013
                    fig.text(0.10, y, f"Follow-up key {fu.get('key') or '—'}", fontsize=7)
                    y -= 0.016
                comm = (it.get("examiner_comment") or "").strip()
                if comm:
                    for ln in _wrap(comm, 98).split("\n")[:5]:
                        if y < 0.10:
                            flush()
                        fig.text(0.08, y, ln, fontsize=7, color="#333")
                        y -= 0.013
                y -= 0.012
            pdf.savefig(fig)
            plt.close(fig)
    return buf.getvalue()


def main() -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"practice http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
