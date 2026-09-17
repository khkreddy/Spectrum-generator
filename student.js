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
      "<div class='name'>" + U.esc(U.paperShort(it.uid)) + "</div>" +
      "<div class='meta'>" + U.techBadge(it) + "</div></button>"
    ).join("") || "<p class='muted pad'>No questions match this filter.</p>";
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
      el.innerHTML = "<p class='muted'>No questions in this filter.</p>";
      return;
    }
    const letters = U.letterSelect(it);
    el.innerHTML =
      "<div class='q-scroll' id='q-scroll'>" +
        "<div class='uid'>" + U.esc(U.paperLabel(it.uid)) + " " + U.techBadge(it) + "</div>" +
        "<div class='q-body'>" +
          (U.showsStem(it) ? U.stemHtml(it.stem) : "") +
          U.figureHtml(it) +
          "<ul class='opts" + (letters ? " letters" : "") + "' id='opts'>" +
            U.optionList(it.options, letters, "opt") +
          "</ul>" +
        "</div>" +
        "<p class='actions'>" +
          "<button class='act' type='button' id='check'>Check</button> " +
          "<button class='ghost' type='button' id='print-one'>Print</button>" +
        "</p>" +
        "<p class='err' id='msg'></p>" +
        "<div id='dock'></div>" +
      "</div>";
    $("check").onclick = grade;
    $("print-one").onclick = () => window.print();
  }

  function setDock(html) {
    const dock = $("dock");
    if (dock) dock.innerHTML = html || "";
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

  function picked(name) {
    const el = document.querySelector("input[name='" + (name || "opt") + "']:checked");
    return el ? el.value : null;
  }

  async function grade() {
    const it = current();
    const choice = picked("opt");
    const msg = $("msg");
    if (!choice) { msg.textContent = "Select A, B, C or D."; return; }
    const j = await postGrade({ uid: it.uid, choice: choice, stage: "item" });
    if (j.error) { msg.textContent = j.error; return; }
    document.querySelectorAll("#opts label").forEach((lab) => {
      lab.classList.toggle("pick", lab.querySelector("input").value === choice);
    });
    if (j.ok) {
      document.querySelectorAll("#opts li").forEach((li) => {
        const v = li.querySelector("input").value;
        li.classList.toggle("ok", v === j.correct);
      });
      msg.className = "okmsg";
      msg.textContent = "Correct.";
      let fb = "";
      if (j.solve) fb += "<div class='comment'>" + U.esc(j.solve) + "</div>";
      if (j.examiner_comment) fb += "<div class='comment'>" + U.esc(j.examiner_comment) + "</div>";
      setDock(fb);
      return;
    }
    if (j.followup) {
      S.mode = "followup";
      S.fromChoice = j.from_choice;
      S.followup = j.followup;
      msg.textContent = "";
      msg.className = "err";
      const fu = j.followup;
      setDock(
        "<div class='hint-box'>" +
          "<p class='prompt'>A related question</p>" +
          U.stemHtml(fu.stem) +
          "<ul class='opts' id='fu-opts'>" + U.optionList(fu.options, false, "fu") + "</ul>" +
          "<p class='actions'><button class='act' type='button' id='check-fu'>Check</button></p>" +
          "<p class='err' id='fu-msg'></p>" +
          "<div id='fu-fb'></div>" +
        "</div>"
      );
      $("check-fu").onclick = gradeFollowup;
      return;
    }
    msg.className = "err";
    msg.textContent = "That is not the answer.";
  }

  async function gradeFollowup() {
    const it = current();
    const choice = picked("fu");
    const msg = $("fu-msg") || $("msg");
    if (!choice) { msg.textContent = "Select A, B, C or D."; return; }
    const j = await postGrade({
      uid: it.uid, choice: choice, stage: "followup", from_choice: S.fromChoice,
    });
    if (j.error) { msg.textContent = j.error; return; }
    document.querySelectorAll("#fu-opts li").forEach((li) => {
      const v = li.querySelector("input").value;
      li.classList.toggle("ok", v === j.correct);
      li.classList.toggle("bad", v === j.choice && !j.ok);
    });
    msg.className = j.ok ? "okmsg" : "err";
    msg.textContent = j.ok ? "Yes." : "The answer is " + j.correct + ".";
    let fb = "";
    if (j.why) fb += "<div class='comment'>" + U.esc(j.why) + "</div>";
    fb += "<p class='prompt'>This question's answer is " + U.esc(j.original_key) + ".</p>";
    if (j.solve) fb += "<div class='comment'>" + U.esc(j.solve) + "</div>";
    if (j.examiner_comment) fb += "<div class='comment'>" + U.esc(j.examiner_comment) + "</div>";
    const box = $("fu-fb");
    if (box) box.innerHTML = fb;
  }

  document.addEventListener("keydown", (e) => {
    if (e.target && /textarea/i.test(e.target.tagName)) return;
    const k = e.key.toUpperCase();
    if (U.LETTERS.indexOf(k) >= 0) {
      const name = S.mode === "followup" ? "fu" : "opt";
      const radio = document.querySelector("input[name='" + name + "'][value='" + k + "']");
      if (radio && !radio.disabled) {
        radio.checked = true;
        e.preventDefault();
      }
    } else if (e.key === "Enter") {
      const btn = S.mode === "followup" ? $("check-fu") : $("check");
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
          show_figure: it.show_figure,
          show_stem: it.show_stem,
          show_option_text: it.show_option_text,
          letter_select: it.letter_select,
          prompt_in_figure: it.prompt_in_figure,
          original_base64: it.show_figure === false ? null : it.original_base64,
          original_url: it.show_figure === false ? null : it.original_url,
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
