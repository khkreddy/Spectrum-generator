(function () {
  const U = window.SpectraUI;
  const S = {
    all: [], items: [], uid: null, mode: "item",
    fromChoice: null, followup: null, shuffled: false,
  };

  function $(id) { return document.getElementById(id); }

  function current() { return S.items.find((x) => x.uid === S.uid); }

  function applyFilter() {
    const sel = U.selectedSet($("filters"));
    let items = U.filterItems(S.all, sel);
    if (S.shuffled) items = U.shuffle(items);
    S.items = items;
    if (!items.find((x) => x.uid === S.uid)) S.uid = items[0] && items[0].uid;
    S.mode = "item";
    S.followup = null;
    renderList();
    renderPaper();
    const n = $("count");
    if (n) n.textContent = items.length + " question" + (items.length === 1 ? "" : "s");
  }

  function renderFilters() {
    const c = U.counts(S.all);
    const start = new Set(U.TECH.map((t) => t.id).filter((id) => (c[id] || 0) > 0));
    $("filters").innerHTML = U.filterBar(S.all, start);
    $("filters").onchange = applyFilter;
    const note = $("nmr-note");
    if (note) note.hidden = (c.nmr || 0) > 0;
  }

  function renderList() {
    $("list").innerHTML = S.items.map((it) =>
      "<button type='button' data-uid='" + U.esc(it.uid) + "' class='" + (it.uid === S.uid ? "on" : "") + "'>" +
      "<div class='uid'>" + U.esc(it.uid) + "</div>" +
      "<div class='meta'>" + U.techBadge(it) + "</div></button>"
    ).join("") || "<p class='muted pad'>No questions in this selection. Turn on Infrared, mass spectrometry, or combined techniques.</p>";
    $("list").onclick = (e) => {
      const b = e.target.closest("button[data-uid]");
      if (!b) return;
      S.uid = b.getAttribute("data-uid");
      S.mode = "item";
      S.fromChoice = null;
      S.followup = null;
      renderList();
      renderPaper();
    };
  }

  function renderPaper() {
    const it = current();
    const el = $("paper");
    if (!it) {
      el.innerHTML = "<p class='muted'>No MCQ in this filter. NMR items in the harvest are paper-4 structured responses, not A–D.</p>";
      return;
    }
    if (S.mode === "followup" && S.followup) {
      const fu = S.followup;
      el.innerHTML =
        "<div class='uid'>" + U.esc(it.uid) + " · follow-up</div>" +
        "<p class='prompt'>Not that option. Think about this first:</p>" +
        U.stemHtml(fu.stem) +
        "<ul class='opts' id='opts'>" + U.optionList(fu.options, false) + "</ul>" +
        "<p class='actions'><button class='act' type='button' id='check'>Check follow-up</button></p>" +
        "<p class='err' id='msg'></p>" +
        "<div id='feedback'></div>";
      $("check").onclick = gradeFollowup;
      return;
    }
    el.innerHTML =
      "<div class='uid'>" + U.esc(it.uid) + " " + U.techBadge(it) + "</div>" +
      U.stemHtml(it.stem) +
      U.figureHtml(it) +
      "<ul class='opts' id='opts'>" + U.optionList(it.options, it.options_are_figure) + "</ul>" +
      "<p class='actions'>" +
      "<button class='act' type='button' id='check'>Check</button> " +
      "<button class='ghost' type='button' id='print-one'>Print this question</button>" +
      "</p>" +
      "<p class='err' id='msg'></p>" +
      "<div id='feedback'></div>";
    $("check").onclick = grade;
    $("print-one").onclick = () => window.print();
  }

  async function postGrade(payload) {
    try {
      const r = await fetch("/api/grade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (r.ok) return r.json();
    } catch (e) { /* static fallback */ }
    return gradeLocal(payload);
  }

  async function gradeLocal(payload) {
    if (!S.lbs) {
      const r = await fetch("lbs.json");
      S.lbs = await r.json();
    }
    const rec = (S.lbs.items || {})[payload.uid] || {};
    if (payload.stage === "followup") {
      const row = (rec.wrong || {})[payload.from_choice] || {};
      const fu = row.followup || {};
      const ok = payload.choice === fu.key;
      return {
        ok, correct: fu.key, why: fu.why, original_key: rec.key || current().key,
        solve: rec.solve, examiner_comment: rec.examiner_comment,
        from_choice: payload.from_choice, stage: "followup",
      };
    }
    const key = rec.key || (current() && current().key);
    const ok = payload.choice === key;
    if (ok) return { ok: true, correct: key, solve: rec.solve, examiner_comment: rec.examiner_comment, stage: "item" };
    const row = (rec.wrong || {})[payload.choice] || {};
    return { ok: false, followup: row.followup, from_choice: payload.choice, stage: "item" };
  }

  async function grade() {
    const it = current();
    const picked = document.querySelector("input[name=opt]:checked");
    const msg = $("msg");
    if (!picked) { msg.textContent = "Choose A, B, C or D."; return; }
    const j = await postGrade({ uid: it.uid, choice: picked.value, stage: "item" });
    if (j.error) { msg.textContent = j.error; return; }
    document.querySelectorAll("#opts label").forEach((lab) => {
      lab.classList.toggle("pick", lab.querySelector("input").value === picked.value);
    });
    if (j.ok) {
      document.querySelectorAll("#opts li").forEach((li) => {
        const v = li.querySelector("input").value;
        li.classList.toggle("ok", v === j.correct);
      });
      msg.className = "okmsg";
      msg.textContent = "Correct.";
      let fb = "";
      if (j.solve) fb += "<h3>How to see it</h3><div class='comment'>" + U.esc(j.solve) + "</div>";
      if (j.examiner_comment) fb += "<h3>Examiner comment</h3><div class='comment'>" + U.esc(j.examiner_comment) + "</div>";
      $("feedback").innerHTML = fb;
      return;
    }
    if (j.followup) {
      S.mode = "followup";
      S.fromChoice = j.from_choice;
      S.followup = j.followup;
      renderPaper();
      return;
    }
    msg.className = "err";
    msg.textContent = "Not " + picked.value + ".";
  }

  async function gradeFollowup() {
    const it = current();
    const picked = document.querySelector("input[name=opt]:checked");
    const msg = $("msg");
    if (!picked) { msg.textContent = "Choose A, B, C or D."; return; }
    const j = await postGrade({
      uid: it.uid, choice: picked.value, stage: "followup", from_choice: S.fromChoice,
    });
    if (j.error) { msg.textContent = j.error; return; }
    document.querySelectorAll("#opts li").forEach((li) => {
      const v = li.querySelector("input").value;
      li.classList.toggle("ok", v === j.correct);
      li.classList.toggle("bad", v === j.choice && !j.ok);
    });
    msg.className = j.ok ? "okmsg" : "err";
    msg.textContent = j.ok
      ? "Yes. Now return to the original question."
      : "Not quite. The follow-up key is " + j.correct + ".";
    let fb = "";
    if (j.why) fb += "<div class='comment'>" + U.esc(j.why) + "</div>";
    fb += "<p class='prompt'>Original question: the key is <b>" + U.esc(j.original_key) + "</b>.</p>";
    if (j.solve) fb += "<h3>How to see it</h3><div class='comment'>" + U.esc(j.solve) + "</div>";
    if (j.examiner_comment) fb += "<h3>Examiner comment</h3><div class='comment'>" + U.esc(j.examiner_comment) + "</div>";
    fb += "<p><button class='ghost' type='button' id='back'>Back to question</button></p>";
    $("feedback").innerHTML = fb;
    $("back").onclick = () => {
      S.mode = "item";
      S.followup = null;
      renderPaper();
    };
  }

  document.addEventListener("keydown", (e) => {
    if (e.target && /input|textarea|select/i.test(e.target.tagName) && e.target.type !== "radio" && e.target.type !== "checkbox") return;
    const k = e.key.toUpperCase();
    if (U.LETTERS.indexOf(k) >= 0) {
      const radio = document.querySelector("input[name=opt][value='" + k + "']");
      if (radio) { radio.checked = true; e.preventDefault(); }
    } else if (e.key === "Enter") {
      const btn = $("check");
      if (btn) { btn.click(); e.preventDefault(); }
    }
  });

  $("shuffle").onclick = () => { S.shuffled = true; applyFilter(); };
  $("order").onclick = () => { S.shuffled = false; applyFilter(); };
  $("print-set").onclick = () => {
    const host = $("print-paper");
    host.innerHTML = S.items.map((it, i) => U.paperArticle(it, i)).join("");
    window.print();
  };
  window.addEventListener("afterprint", () => {
    const host = $("print-paper");
    if (host) host.innerHTML = "";
  });

  async function boot() {
    let doc;
    try {
      const r = await fetch("/api/catalog");
      if (r.ok) doc = await r.json();
    } catch (e) { doc = null; }
    if (!doc) {
      const pack = await (await fetch("pack.json")).json();
      doc = {
        items: (pack.items || []).filter((it) => it.options && it.key).map((it) => ({
          uid: it.uid,
          spectrum_types: it.spectrum_types,
          technique: it.technique,
          item_type: it.item_type,
          stem: it.stem,
          options: it.options,
          options_are_figure: it.options_are_figure,
          original_base64: it.original_base64,
          original_url: it.original_url,
          has_examiner_comment: !!it.examiner_comment,
          has_lbs: it.has_lbs,
        })),
      };
    }
    S.all = doc.items || [];
    renderFilters();
    applyFilter();
  }
  boot();
})();
