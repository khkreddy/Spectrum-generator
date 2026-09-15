(function () {
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function mountTikz(root) {
    root.querySelectorAll(".tikz-slot").forEach((slot) => {
      if (slot.querySelector("script[type='text/tikz']")) return;
      const pre = slot.querySelector(".tikz-src");
      if (!pre) return;
      const s = document.createElement("script");
      s.type = "text/tikz";
      s.textContent = pre.textContent;
      pre.remove();
      slot.appendChild(s);
    });
  }

  function show(j) {
    const out = $("out");
    out.hidden = false;
    out.innerHTML =
      "<div class='uid'>" + esc(j.name) + " · " + esc(j.smiles) + " · " + esc(j.formula) +
      " · family " + esc(j.family) + "</div>" +
      (j.tikz
        ? "<div class='tikz-slot'><pre class='tikz-src' hidden>" + esc(j.tikz) + "</pre><p class='muted'>Drawing IR…</p></div>"
        : "<p class='muted'>No IR.</p>");
    mountTikz(out);
  }

  async function run(molecule) {
    const err = $("err");
    const out = $("out");
    err.textContent = "";
    out.hidden = true;
    try {
      const r = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ molecule }),
      });
      const j = await r.json();
      if (r.ok) { show(j); return; }
      err.textContent = j.error || r.statusText;
      if (r.status !== 404) return;
    } catch (e) { /* static */ }
    if (!S.examples) {
      try {
        S.examples = (await (await fetch("ir_examples.json")).json()).examples || [];
      } catch (e2) {
        err.textContent = "Generator needs the local Python server for arbitrary SMILES.";
        return;
      }
    }
    const q = molecule.trim().toLowerCase();
    const hit = S.examples.find((ex) =>
      ex.name.toLowerCase() === q || ex.smiles.toLowerCase() === q
    );
    if (!hit) {
      err.textContent = "On GitHub Pages only the named examples are precomputed. Run the Python generator locally for other SMILES.";
      return;
    }
    show(hit);
  }

  const S = { examples: null };

  $("f").onsubmit = (e) => {
    e.preventDefault();
    const v = $("mol").value.trim();
    if (v) run(v);
  };
  document.querySelectorAll("[data-m]").forEach((a) => {
    a.onclick = (e) => {
      e.preventDefault();
      $("mol").value = a.getAttribute("data-m");
      run($("mol").value);
    };
  });
})();
