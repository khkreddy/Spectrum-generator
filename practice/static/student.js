(function () {
  const S = { items: [], uid: null, mode: "item", fromChoice: null, followup: null };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function chem(s) {
    return esc(s).replace(/&lt;sub&gt;/gi, "<sub>").replace(/&lt;\/sub&gt;/gi, "</sub>")
      .replace(/&lt;sup&gt;/gi, "<sup>").replace(/&lt;\/sup&gt;/gi, "</sup>");
  }
  function current() { return S.items.find((x) => x.uid === S.uid); }

  function optionList(options, figure) {
    return ["A", "B", "C", "D"].map((k) => {
      if (!(options && Object.prototype.hasOwnProperty.call(options, k)) && !figure) return "";
      const text = (options && options[k]) || "";
      const body = text ? "<span class='opt-text'>" + chem(text) + "</span>" : "";
      return (
        "<li><label class='opt" + (figure || !text ? " letter-only" : "") + "'>" +
        "<input type='radio' name='opt' value='" + k + "'>" +
        "<span class='letter'>" + k + "</span>" + body +
        "</label></li>"
      );
    }).join("");
  }

  function renderList() {
    $("list").innerHTML = S.items.map((it) =>
      "<button type='button' data-uid='" + esc(it.uid) + "' class='" + (it.uid === S.uid ? "on" : "") + "'>" +
      "<div class='uid'>" + esc(it.uid) + "</div>" +
      "<div class='meta'>" + esc((it.spectrum_types || []).join(" · ")) + "</div></button>"
    ).join("");
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
    if (!it) { el.innerHTML = "<p class='muted'>No MCQ items.</p>"; return; }
    const img = it.original_base64
      ? "<img class='orig' src='" + it.original_base64 + "' alt='exam figure'>"
      : "";
    if (S.mode === "followup" && S.followup) {
      const fu = S.followup;
      el.innerHTML =
        "<div class='uid'>" + esc(it.uid) + " · follow-up</div>" +
        "<p class='prompt'>Not that option. Think about this first:</p>" +
        "<p class='stem'>" + chem(fu.stem) + "</p>" +
        "<ul class='opts' id='opts'>" + optionList(fu.options, false) + "</ul>" +
        "<p><button class='act' type='button' id='check'>Check follow-up</button></p>" +
        "<p class='err' id='msg'></p>" +
        "<div id='feedback'></div>";
      $("check").onclick = gradeFollowup;
      return;
    }
    el.innerHTML =
      "<div class='uid'>" + esc(it.uid) + "</div>" +
      "<p class='stem'>" + chem(it.stem) + "</p>" +
      img +
      "<ul class='opts' id='opts'>" + optionList(it.options, it.options_are_figure) + "</ul>" +
      "<p><button class='act' type='button' id='check'>Check</button></p>" +
      "<p class='err' id='msg'></p>" +
      "<div id='feedback'></div>";
    $("check").onclick = grade;
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
        ok, correct: fu.key, why: fu.why, original_key: rec.key, solve: rec.solve,
        examiner_comment: rec.examiner_comment, from_choice: payload.from_choice, stage: "followup",
      };
    }
    const ok = payload.choice === rec.key;
    if (ok) return { ok: true, correct: rec.key, solve: rec.solve, examiner_comment: rec.examiner_comment, stage: "item" };
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
      if (j.solve) fb += "<h3>How to see it</h3><div class='comment'>" + esc(j.solve) + "</div>";
      if (j.examiner_comment) fb += "<h3>Examiner comment</h3><div class='comment'>" + esc(j.examiner_comment) + "</div>";
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
    if (j.why) fb += "<div class='comment'>" + esc(j.why) + "</div>";
    fb += "<p class='prompt'>Original question: the key is <b>" + esc(j.original_key) + "</b>.</p>";
    if (j.solve) fb += "<h3>How to see it</h3><div class='comment'>" + esc(j.solve) + "</div>";
    if (j.examiner_comment) fb += "<h3>Examiner comment</h3><div class='comment'>" + esc(j.examiner_comment) + "</div>";
    fb += "<p><button class='ghost' type='button' id='back'>Back to question</button></p>";
    $("feedback").innerHTML = fb;
    $("back").onclick = () => {
      S.mode = "item";
      S.followup = null;
      renderPaper();
    };
  }

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
          stem: it.stem,
          options: it.options,
          options_are_figure: it.options_are_figure,
          original_base64: it.original_base64,
          has_examiner_comment: !!it.examiner_comment,
          has_lbs: it.has_lbs,
        })),
      };
    }
    S.items = doc.items || [];
    S.uid = S.items[0] && S.items[0].uid;
    renderList();
    renderPaper();
  }
  boot();
})();
