(function () {
  const U = window.SpectraUI;
  let all = [];
  let items = [];
  const $ = (id) => document.getElementById(id);

  function applyFilter() {
    const sel = U.selectedSet($("filters"));
    items = U.filterItems(all, sel);
    render();
    renderPrint();
    $("count").textContent = items.length + " question" + (items.length === 1 ? "" : "s");
  }

  function renderFilters() {
    const c = U.counts(all);
    const start = new Set(U.TECH.map((t) => t.id).filter((id) => (c[id] || 0) > 0));
    $("filters").innerHTML = U.filterBar(all, start);
    $("filters").onchange = applyFilter;
    $("nmr-note").hidden = (c.nmr || 0) > 0;
  }

  function render() {
    $("tbl").innerHTML =
      "<tr><th></th><th>uid</th><th>technique</th><th>key</th><th>LBS</th><th>figure</th><th>examiner</th></tr>" +
      items.map((it, i) =>
        "<tr><td><input type='checkbox' data-i='" + i + "' checked></td>" +
        "<td class='mono'>" + U.esc(it.uid) + "</td>" +
        "<td>" + U.techBadge(it) + "</td>" +
        "<td>" + U.esc(it.key || "—") + "</td>" +
        "<td>" + (it.lbs || it.has_lbs ? "yes" : "") + "</td>" +
        "<td>" + (it.show_figure || it.original_base64 || it.original_url ? "yes" : "") + "</td>" +
        "<td>" + (it.examiner_comment ? "yes" : "") + "</td></tr>"
      ).join("");
  }

  function selectedItems() {
    const boxes = [...document.querySelectorAll("input[data-i]:checked")];
    if (!boxes.length) return [];
    return boxes.map((el) => items[+el.getAttribute("data-i")]).filter(Boolean);
  }

  $("all").onclick = () => {
    document.querySelectorAll("input[data-i]").forEach((el) => { el.checked = true; });
    renderPrint();
  };
  $("none").onclick = () => {
    document.querySelectorAll("input[data-i]").forEach((el) => { el.checked = false; });
    renderPrint();
  };

  $("dl").onclick = async () => {
    const err = $("err");
    err.textContent = "";
    const chosen = selectedItems();
    if (!chosen.length) { err.textContent = "Select at least one question."; return; }
    try {
      const r = await fetch("/api/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uids: chosen.map((it) => it.uid), answers: $("answers").checked }),
      });
      if (r.ok) {
        const blob = await r.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "9701-spectra-pack.pdf";
        a.click();
        return;
      }
    } catch (e) { /* print fallback */ }
    err.textContent = "PDF server is not running — use Print for a paper + answer key.";
    window.print();
  };

  $("print").onclick = () => window.print();

  function renderPrint() {
    const chosen = selectedItems();
    const paper = $("print-paper");
    const key = $("print-key");
    paper.innerHTML = chosen.map((it, n) => U.paperArticle(it, n)).join("");
    if (!$("answers").checked) { key.innerHTML = ""; return; }
    key.innerHTML = "<h2>Answer key · learn-by-solve</h2>" + chosen.map((it, n) => {
      const lbs = it.lbs || {};
      const wrong = lbs.wrong || {};
      const rows = U.LETTERS.filter((k) => k !== it.key).map((k) => {
        const row = wrong[k] || {};
        const fu = row.followup || {};
        return "<li><b>If " + k + "</b> [" + U.esc(row.mx_type || "") + "] " +
          U.esc(row.pathway || "") +
          (fu.stem ? "<br><i>Follow-up:</i> " + U.esc(fu.stem) + " (key " + U.esc(fu.key || "") + ")" : "") +
          "</li>";
      }).join("");
      return "<article class='key-block'><h3>" + (n + 1) + ". " + U.esc(it.uid) + " → " + U.esc(it.key || "—") +
        "</h3>" + U.stemHtml(it.stem) + U.figureHtml(it, "orig small") +
        "<p>" + U.esc(lbs.solve || "") + "</p><ul>" + rows + "</ul>" +
        (it.examiner_comment ? "<p class='comment'>" + U.esc(it.examiner_comment) + "</p>" : "") +
        "</article>";
    }).join("");
  }

  document.addEventListener("change", (e) => {
    if (e.target && e.target.matches("input[data-i], #answers")) renderPrint();
  });

  function boot(doc) {
    all = (doc.items || []).filter((it) => it.options && it.key);
    renderFilters();
    applyFilter();
  }

  fetch("/api/teacher-catalog").then((r) => {
    if (!r.ok) throw new Error("no api");
    return r.json();
  }).then(boot).catch(async () => {
    const pack = await (await fetch("pack.json")).json();
    const lbs = await (await fetch("lbs.json")).json().catch(() => ({ items: {} }));
    (pack.items || []).forEach((it) => { it.lbs = (lbs.items || {})[it.uid]; });
    boot(pack);
  });
})();
