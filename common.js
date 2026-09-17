(function (global) {
  const LETTERS = ["A", "B", "C", "D"];
  const TECH = [
    { id: "ir", label: "Infrared", short: "IR" },
    { id: "ms", label: "Mass spectrometry", short: "MS" },
    { id: "nmr", label: "NMR", short: "NMR" },
    { id: "mixed", label: "Combined techniques", short: "Mixed" },
  ];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function chem(s) {
    return esc(s)
      .replace(/&lt;sub&gt;/gi, "<sub>").replace(/&lt;\/sub&gt;/gi, "</sub>")
      .replace(/&lt;sup&gt;/gi, "<sup>").replace(/&lt;\/sup&gt;/gi, "</sup>");
  }

  function techniqueOf(it) {
    if (it.technique) return it.technique;
    const t = it.spectrum_types || [];
    if (t.length > 1) return "mixed";
    return (t[0] || "other").toLowerCase();
  }

  function counts(items) {
    const c = { ir: 0, ms: 0, nmr: 0, mixed: 0, other: 0 };
    (items || []).forEach((it) => { c[techniqueOf(it)] = (c[techniqueOf(it)] || 0) + 1; });
    return c;
  }

  function selectedSet(root) {
    const boxes = [...(root || document).querySelectorAll("input[data-tech]")];
    if (!boxes.length) return null;
    const on = boxes.filter((b) => b.checked).map((b) => b.getAttribute("data-tech"));
    return on.length ? new Set(on) : new Set();
  }

  function filterItems(items, selected) {
    if (!selected) return items.slice();
    if (selected.size === 0) return [];
    return items.filter((it) => selected.has(techniqueOf(it)));
  }

  function filterBar(items, selected, extraClass) {
    const c = counts(items);
    const sel = selected || new Set(TECH.map((t) => t.id).filter((id) => c[id] > 0));
    const chips = TECH.filter((t) => (c[t.id] || 0) > 0).map((t) => {
      const n = c[t.id] || 0;
      const checked = sel.has(t.id) ? " checked" : "";
      return (
        "<label class='chip'>" +
        "<input type='checkbox' data-tech='" + t.id + "'" + checked + ">" +
        "<span>" + t.label + " <b>" + n + "</b></span></label>"
      );
    }).join("");
    return "<div class='filters " + (extraClass || "") + "'>" + chips + "</div>";
  }

  function tableHtml(lines) {
    const rows = lines.filter((l) => l.includes("|")).map((l) => {
      const cells = l.split("|").map((c) => c.trim());
      if (cells[0] === "") cells.shift();
      if (cells.length && cells[cells.length - 1] === "") cells.pop();
      return cells;
    });
    if (!rows.length) return "";
    const head = rows[0];
    const body = rows.slice(1).filter((r) => !r.every((c) => /^[-–:]+$/.test(c)));
    let html = "<table class='stem-table'><thead><tr>";
    head.forEach((c) => { html += "<th>" + chem(c) + "</th>"; });
    html += "</tr></thead><tbody>";
    body.forEach((r) => {
      html += "<tr>";
      r.forEach((c) => { html += "<td>" + chem(c) + "</td>"; });
      html += "</tr>";
    });
    html += "</tbody></table>";
    return html;
  }

  function stemHtml(stem) {
    const text = String(stem || "").trim();
    if (!text) return "";
    const blocks = text.split(/\n{2,}/);
    return blocks.map((block) => {
      const lines = block.split("\n");
      const pipe = lines.filter((l) => l.includes("|")).length;
      if (pipe >= 2) return tableHtml(lines);
      return "<p class='stem'>" + chem(block) + "</p>";
    }).join("");
  }

  function showsFigure(it) {
    if (it.show_figure === false) return false;
    if (it.show_figure === true) return true;
    return !!(it.original_base64 || it.original_url);
  }
  function showsStem(it) {
    if (it.show_stem === false) return false;
    return true;
  }
  function letterSelect(it) {
    return !!(it.letter_select || it.options_are_figure || it.prompt_in_figure);
  }

  function figureHtml(it, cls) {
    if (!showsFigure(it)) return "";
    const src = it.original_base64 || it.original_url;
    if (!src) return "";
    return "<img class='" + (cls || "orig") + "' src='" + src + "' alt='Exam figure'>";
  }

  function optionList(options, figure, name) {
    const nm = name || "opt";
    return LETTERS.map((k) => {
      if (!(options && Object.prototype.hasOwnProperty.call(options, k)) && !figure) return "";
      const text = figure ? "" : ((options && options[k]) || "");
      const body = text ? "<span class='opt-text'>" + chem(text) + "</span>" : "";
      return (
        "<li><label class='opt" + (figure || !text ? " letter-only" : "") + "'>" +
        "<input type='radio' name='" + nm + "' value='" + k + "'>" +
        "<span class='letter'>" + k + "</span>" + body +
        "</label></li>"
      );
    }).join("");
  }

  function techBadge(it) {
    const t = techniqueOf(it);
    const meta = TECH.find((x) => x.id === t);
    const label = meta ? meta.short : t;
    const extra = (it.spectrum_types || []).join(" · ");
    return "<span class='badge b-" + t + "'>" + esc(label) + "</span>" +
      (extra && extra !== t ? "<span class='meta'>" + esc(extra) + "</span>" : "");
  }

  const SEASON = { m: "March", s: "June", w: "November" };
  function paperParts(uid) {
    const m = String(uid || "").match(/^9701_([msw])(\d{2})_qp_(\d+):q(\d+)$/i);
    if (!m) return null;
    return {
      season: SEASON[m[1].toLowerCase()] || m[1],
      year: 2000 + parseInt(m[2], 10),
      paper: m[3],
      q: m[4],
    };
  }
  function paperLabel(uid) {
    const p = paperParts(uid);
    if (!p) return uid || "";
    return p.season + " " + p.year + " paper " + p.paper + ", question " + p.q;
  }
  function paperShort(uid) {
    const p = paperParts(uid);
    if (!p) return uid || "";
    return p.season + " " + p.year + " · Q" + p.q;
  }

  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function paperArticle(it, n) {
    const img = figureHtml(it);
    const letters = letterSelect(it);
    const opts = LETTERS.map((k) => {
      const t = letters ? "" : ((it.options || {})[k] || "");
      if (!t) return "<div class='opt-line'><b>" + k + "</b></div>";
      return "<div class='opt-line'><b>" + k + "</b> " + chem(t) + "</div>";
    }).join("");
    const num = n != null ? (n + 1) + ". " : "";
    return "<article class='paper print-q'><div class='uid'>" + num + esc(paperLabel(it.uid)) +
      " " + techBadge(it) + "</div>" +
      (showsStem(it) ? stemHtml(it.stem) : "") + img +
      "<ul class='opts print-opts'>" + opts + "</ul></article>";
  }

  global.SpectraUI = {
    LETTERS, TECH, esc, chem, techniqueOf, counts, selectedSet, filterItems,
    filterBar, stemHtml, figureHtml, optionList, techBadge, shuffle, paperArticle,
    showsFigure, showsStem, letterSelect, paperLabel, paperShort,
  };
})(window);
