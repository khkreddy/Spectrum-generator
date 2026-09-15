(function () {
  let items = [];
  const $ = (id) => document.getElementById(id);

  function render() {
    $("tbl").innerHTML =
      "<tr><th></th><th>uid</th><th>type</th><th>key</th><th>LBS</th><th>examiner</th></tr>" +
      items.map((it, i) =>
        "<tr><td><input type='checkbox' data-i='" + i + "' " +
        (it.key ? "checked" : "") + "></td>" +
        "<td class='mono'>" + it.uid + "</td>" +
        "<td>" + (it.spectrum_types || []).join(", ") + "</td>" +
        "<td>" + (it.key || "—") + "</td>" +
        "<td>" + (it.lbs ? "yes" : "") + "</td>" +
        "<td>" + (it.examiner_comment ? "yes" : "") + "</td></tr>"
      ).join("");
  }

  function selected() {
    return [...document.querySelectorAll("input[data-i]:checked")].map((el) => items[+el.getAttribute("data-i")].uid);
  }

  $("all").onclick = () => {
    document.querySelectorAll("input[data-i]").forEach((el) => { el.checked = true; });
  };
  $("none").onclick = () => document.querySelectorAll("input[data-i]").forEach((el) => { el.checked = false; });

  $("dl").onclick = async () => {
    const err = $("err");
    err.textContent = "";
    const uids = selected();
    if (!uids.length) { err.textContent = "Select at least one question."; return; }
    try {
      const r = await fetch("/api/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uids, answers: $("answers").checked }),
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
    const uids = new Set(selected());
    const chosen = items.filter((it) => uids.has(it.uid));
    const paper = $("print-paper");
    const key = $("print-key");
    paper.innerHTML = chosen.map((it, n) => {
      const img = it.original_base64
        ? "<img class='orig' src='" + it.original_base64 + "' alt=''>"
        : "";
      const opts = ["A", "B", "C", "D"].map((k) => {
        const t = (it.options || {})[k] || "";
        if (it.options_are_figure || !t) return "<div class='opt-line'><b>" + k + "</b></div>";
        return "<div class='opt-line'><b>" + k + "</b> " + t + "</div>";
      }).join("");
      return "<article class='paper print-q'><div class='uid'>" + (n + 1) + ". " + it.uid +
        "</div><p class='stem'>" + (it.stem || "") + "</p>" + img + opts + "</article>";
    }).join("");
    key.innerHTML = "<h2>Answer key</h2>" + chosen.map((it, n) => {
      const lbs = it.lbs || {};
      const wrong = lbs.wrong || {};
      const rows = ["A", "B", "C", "D"].filter((k) => k !== it.key).map((k) => {
        const row = wrong[k] || {};
        const fu = row.followup || {};
        return "<li><b>If " + k + "</b> [" + (row.mx_type || "") + "] " +
          (row.pathway || "") +
          (fu.stem ? "<br><i>Follow-up:</i> " + fu.stem + " (key " + (fu.key || "") + ")" : "") +
          "</li>";
      }).join("");
      return "<article class='key-block'><h3>" + (n + 1) + ". " + it.uid + " → " + (it.key || "—") +
        "</h3><p>" + (lbs.solve || "") + "</p><ul>" + rows + "</ul>" +
        (it.examiner_comment ? "<p class='comment'>" + it.examiner_comment + "</p>" : "") +
        "</article>";
    }).join("");
  }

  document.addEventListener("change", (e) => {
    if (e.target && e.target.matches("input[data-i], #answers")) renderPrint();
  });

  function boot(doc) {
    items = doc.items || [];
    render();
    renderPrint();
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
