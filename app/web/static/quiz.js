/* 八股复习系统前端：评分浮条 + 遗忘曲线 + 会话时间轴 + AI 详解/追问/复盘 */
(function () {
  "use strict";
  var FACTOR = 19 / 81, DECAY = -0.5;
  var RATE_LABEL = {1: "忘了", 2: "困难", 3: "记得", 4: "简单"};

  function pwd() {
    var p = "";
    try { p = sessionStorage.getItem("radar-pwd") || ""; } catch (e) {}
    if (!p) {
      p = window.prompt("管理密码（用户名 admin）") || "";
      if (p) { try { sessionStorage.setItem("radar-pwd", p); } catch (e) {} }
    }
    return p;
  }
  function authFetch(url, body) {
    var p = pwd();
    if (!p) { return Promise.reject(new Error("未输入密码")); }
    return fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json",
                "Authorization": "Basic " + btoa("admin:" + p)},
      body: JSON.stringify(body || {})
    }).then(function (r) {
      if (r.status === 401) {
        try { sessionStorage.removeItem("radar-pwd"); } catch (e) {}
        throw new Error("密码错误，请重试");
      }
      return r.json();
    });
  }
  function esc(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ---------- 遗忘曲线 SVG ---------- */
  function curveSvg(card) {
    var S = Math.max(card.stability || 0.5, 0.1);
    var elapsed = 0;
    if (card.last_review) {
      elapsed = (Date.now() - new Date(card.last_review).getTime()) / 86400000;
    }
    var span = Math.max(S * 2.2, elapsed * 1.2, 7);
    var W = 300, H = 90, n = 60, pts = [];
    for (var i = 0; i <= n; i++) {
      var t = span * i / n;
      var r = Math.pow(1 + FACTOR * t / S, DECAY);
      pts.push((20 + (W - 30) * i / n).toFixed(1) + "," + (10 + (H - 30) * (1 - r)).toFixed(1));
    }
    function x(t) { return 20 + (W - 30) * Math.min(t / span, 1); }
    var rNow = Math.pow(1 + FACTOR * Math.max(elapsed, 0) / S, DECAY);
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" class="fcurve">' +
      '<line x1="20" y1="' + (H - 20) + '" x2="' + (W - 10) + '" y2="' + (H - 20) + '" class="ax"/>' +
      '<line x1="20" y1="10" x2="20" y2="' + (H - 20) + '" class="ax"/>' +
      '<polyline points="' + pts.join(" ") + '" class="cv"/>' +
      '<circle cx="' + x(elapsed) + '" cy="' + (10 + (H - 30) * (1 - rNow)) + '" r="4" class="dot-now"/>' +
      '<text x="22" y="18" class="lb">记忆保持率 R(t)　稳定度 S=' + S.toFixed(1) + '天</text>' +
      '<text x="' + (W - 10) + '" y="' + (H - 6) + '" text-anchor="end" class="lb">' + span.toFixed(0) + '天</text></svg>';
    return svg;
  }

  /* ---------- 题目渲染 ---------- */
  function qHtml(q) {
    var c = q.card || {};
    var rPct = c.retrievability != null ? Math.round(c.retrievability * 100) + "%" : "—";
    return '' +
    '<article class="detail quiz-card" data-qid="' + q.id + '">' +
      '<div class="card-head">' +
        '<span class="badge badge-cat">' + esc(q.domain_label) + '</span>' +
        '<span class="badge badge-src">' + esc(q.category || "") + '</span>' +
        '<span class="badge st' + (c.state || 0) + '">' + esc(c.state_name || "新题") + '</span>' +
        '<span class="muted">保持率 ' + rPct + ' · 复习 ' + (c.reps || 0) + ' 次 · 忘记 ' + (c.lapses || 0) + ' 次</span>' +
        '<button class="link-btn q-star" type="button">' + (q.starred ? "⭐ 已星标" : "☆ 星标") + '</button>' +
      '</div>' +
      '<h1 class="q-title">' + esc(q.question) + '</h1>' +
      '<div class="q-curve">' + curveSvg(c) + '</div>' +
      '<div class="ai-actions">' +
        '<button class="btn-primary q-show" type="button">显示答案</button>' +
        '<button class="btn-test q-explain" type="button">🤖 AI 详解</button>' +
        '<span class="muted q-status"></span>' +
      '</div>' +
      '<div class="q-answer prose" hidden>' + q.answer_html + '</div>' +
      '<div class="q-asksec" hidden>' +
        '<div class="ask-box" style="margin-top:14px">' +
          '<textarea class="q-ask-input" rows="2" maxlength="500" placeholder="针对这道题继续追问…"></textarea>' +
          '<button class="btn-test q-ask-btn" type="button">追问</button>' +
        '</div><div class="q-ask-out prose"></div>' +
      '</div>' +
    '</article>';
  }

  function bindQuestion(root, q, opts) {
    var status = root.querySelector(".q-status");
    root.querySelector(".q-show").addEventListener("click", function () {
      root.querySelector(".q-answer").hidden = false;
      root.querySelector(".q-asksec").hidden = false;
      this.hidden = true;
      showRatebar(q, opts);
    });
    root.querySelector(".q-star").addEventListener("click", function () {
      var btn = this;
      authFetch("/api/quiz/star/" + q.id).then(function (d) {
        btn.textContent = d.starred ? "⭐ 已星标" : "☆ 星标";
      }).catch(function (e) { status.textContent = e.message; });
    });
    root.querySelector(".q-explain").addEventListener("click", function () {
      status.textContent = "AI 详解生成中…";
      authFetch("/api/quiz/explain/" + q.id).then(function (d) {
        if (d.ok) {
          var ans = root.querySelector(".q-answer");
          ans.innerHTML = d.answer_html; ans.hidden = false;
          root.querySelector(".q-asksec").hidden = false;
          var sb = root.querySelector(".q-show"); if (sb) { sb.hidden = true; }
          showRatebar(q, opts);
          status.textContent = "详解已生成（" + d.model + "）";
        } else { status.textContent = "✗ " + d.error; }
      }).catch(function (e) { status.textContent = "✗ " + e.message; });
    });
    root.querySelector(".q-ask-btn").addEventListener("click", function () {
      var input = root.querySelector(".q-ask-input");
      var out = root.querySelector(".q-ask-out");
      var text = input.value.trim();
      if (!text) { return; }
      out.innerHTML = '<p class="muted">思考中…</p>';
      authFetch("/api/quiz/ask/" + q.id, {question: text}).then(function (d) {
        if (!d.ok) { out.textContent = "✗ " + d.error; return; }
        out.innerHTML = d.answer_html +
          '<p><button class="link-btn q-save-ans" type="button">⭐ 收藏此回答</button>' +
          ' <span class="muted">' + d.model + '</span></p>';
        addTimelineNode({type: "ask", qid: q.id, snippet: text.slice(0, 30),
                         rating: 0, time: tNow()});
        out.querySelector(".q-save-ans").addEventListener("click", function () {
          var b = this;
          authFetch("/api/quiz/save_answer", {
            question_id: q.id, title: text.slice(0, 50),
            content_md: "## 追问\n\n" + text + "\n\n## 回答\n\n" + d.answer_md +
                        "\n\n> 题目：" + q.question
          }).then(function () { b.textContent = "✓ 已收藏到笔记"; b.disabled = true; });
        });
      }).catch(function (e) { out.textContent = "✗ " + e.message; });
    });
  }

  /* ---------- 右下角评分浮条 ---------- */
  var ratebar = document.getElementById("quiz-ratebar");
  function showRatebar(q, opts) {
    if (!ratebar) { return; }
    var pv = q.preview || {};
    ratebar.innerHTML = '<div class="rb-tip">评估你对这道题的掌握程度 ↓</div>' +
      [1, 2, 3, 4].map(function (g) {
        return '<button class="rb-btn rb' + g + '" data-g="' + g + '" type="button">' +
          RATE_LABEL[g] + '<small>' + esc(pv[g] || "") + '</small></button>';
      }).join("");
    ratebar.hidden = false;
    Array.prototype.forEach.call(ratebar.querySelectorAll(".rb-btn"), function (b) {
      b.addEventListener("click", function () {
        var g = parseInt(b.dataset.g, 10);
        ratebar.querySelectorAll(".rb-btn").forEach(function (x) { x.disabled = true; });
        authFetch("/api/quiz/rate", {question_id: q.id, rating: g}).then(function (d) {
          if (!d.ok) { throw new Error(d.error || "失败"); }
          addTimelineNode({type: "review", qid: q.id, snippet: q.question.slice(0, 30),
                           rating: g, time: tNow()});
          ratebar.innerHTML = '<div class="rb-tip">✓ ' + esc(d.message) + '</div>';
          if (opts && opts.onRated) { setTimeout(function () { opts.onRated(g, d); }, 600); }
          else { setTimeout(function () { ratebar.hidden = true; }, 2500); }
        }).catch(function (e) {
          ratebar.querySelectorAll(".rb-btn").forEach(function (x) { x.disabled = false; });
          ratebar.querySelector(".rb-tip").textContent = "✗ " + e.message;
        });
      });
    });
  }

  /* ---------- 会话时间轴 ---------- */
  function tNow() {
    var d = new Date();
    return ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
  }
  function tlKey() { return "quiz-tl-" + new Date().toISOString().slice(0, 10); }
  function tlLoad() {
    try { return JSON.parse(sessionStorage.getItem(tlKey()) || "[]"); } catch (e) { return []; }
  }
  function addTimelineNode(node) {
    var arr = tlLoad();
    arr.push(node);
    try { sessionStorage.setItem(tlKey(), JSON.stringify(arr.slice(-80))); } catch (e) {}
    renderTimeline();
  }
  function renderTimeline() {
    var list = document.getElementById("qr-tl-list");
    if (!list) { return; }
    var arr = tlLoad();
    list.innerHTML = arr.map(function (n, i) {
      var cls = n.type === "ask" ? "ask" : "r" + n.rating;
      var tag = n.type === "ask" ? "追问" : (RATE_LABEL[n.rating] || "");
      return '<li class="qtl-node ' + cls + '" data-qid="' + n.qid + '" data-i="' + i + '">' +
        '<span class="qtl-dot"></span><div><a href="#" class="qtl-link">' + esc(n.snippet) + '…</a>' +
        '<span class="muted"> ' + tag + ' · ' + n.time + '</span></div></li>';
    }).reverse().join("");
    Array.prototype.forEach.call(list.querySelectorAll(".qtl-node"), function (li) {
      li.querySelector(".qtl-link").addEventListener("click", function (e) {
        e.preventDefault();
        var qid = parseInt(li.dataset.qid, 10);
        if (window.__qrLoad) { window.__qrLoad(qid); }            // 复习页内跳转定位
        else { window.location.href = "/quiz/q/" + qid; }          // 其它页直接跳转
      });
    });
  }

  /* ---------- 单题页 ---------- */
  var single = document.getElementById("quiz-single");
  if (single) {
    var q = JSON.parse(single.dataset.q);
    single.innerHTML = qHtml(q);
    bindQuestion(single, q, null);
  }

  /* ---------- 复习模式页 ---------- */
  var qrBox = document.getElementById("qr-question");
  if (qrBox) {
    var queue = [], pos = 0, doneCount = 0;
    var prog = document.getElementById("qr-progress");
    function loadQ(qid) {
      fetch("/api/quiz/q/" + qid).then(function (r) { return r.json(); }).then(function (q) {
        qrBox.innerHTML = qHtml(q);
        ratebar.hidden = true;
        bindQuestion(qrBox, q, {onRated: function () { doneCount++; next(); }});
        window.scrollTo({top: 0, behavior: "smooth"});
        prog.textContent = "进度 " + (doneCount) + " / " + queue.length +
          "（剩余 " + Math.max(queue.length - pos, 0) + " 题）";
      });
    }
    window.__qrLoad = function (qid) { loadQ(qid); };   // 时间轴跳转入口
    function next() {
      if (pos >= queue.length) {
        qrBox.innerHTML = "";
        ratebar.hidden = true;
        document.getElementById("qr-done").hidden = false;
        prog.textContent = "完成 " + doneCount + " 题 ✓";
        return;
      }
      loadQ(queue[pos++]);
    }
    fetch("/api/quiz/queue").then(function (r) { return r.json(); }).then(function (d) {
      queue = d.queue || [];
      if (!queue.length) {
        prog.textContent = "当前没有到期题目 🎉";
        document.getElementById("qr-done").hidden = false;
      } else { next(); }
    });
    var retroBtn = document.getElementById("qr-retro");
    if (retroBtn) {
      retroBtn.addEventListener("click", function () {
        retroBtn.disabled = true; retroBtn.textContent = "生成中…";
        authFetch("/api/quiz/retro").then(function (d) {
          var out = document.getElementById("qr-retro-out");
          if (d.ok) {
            out.innerHTML = d.html + '<p><a href="/notes" target="_blank">已存入笔记 →</a></p>';
            retroBtn.textContent = "✓ 已生成";
          } else { out.textContent = "✗ " + d.error; retroBtn.disabled = false; retroBtn.textContent = "重试"; }
        }).catch(function (e) {
          retroBtn.disabled = false; retroBtn.textContent = "重试（" + e.message + "）";
        });
      });
    }
  }
  renderTimeline();

  /* ---------- 概览页：复盘 + AI 出题 ---------- */
  var retroBtn2 = document.getElementById("quiz-retro-btn");
  if (retroBtn2) {
    retroBtn2.addEventListener("click", function () {
      var st = document.getElementById("quiz-ov-status");
      st.textContent = "生成中…";
      authFetch("/api/quiz/retro").then(function (d) {
        if (d.ok) {
          document.getElementById("quiz-retro-out").innerHTML =
            d.html + '<p><a href="/notes" target="_blank">已存入笔记 →</a></p>';
          st.textContent = "✓";
        } else { st.textContent = "✗ " + d.error; }
      }).catch(function (e) { st.textContent = "✗ " + e.message; });
    });
  }
  var genBtn = document.getElementById("gen-btn");
  if (genBtn) {
    genBtn.addEventListener("click", function () {
      var st = document.getElementById("gen-status");
      st.textContent = "出题中…（约 30 秒）";
      genBtn.disabled = true;
      authFetch("/api/quiz/generate", {
        domain: document.getElementById("gen-domain").value,
        n: parseInt(document.getElementById("gen-n").value, 10)
      }).then(function (d) {
        st.textContent = d.ok ? ("✓ 新增 " + d.added + " 题，刷新可见") : ("✗ " + d.error);
      }).catch(function (e) { st.textContent = "✗ " + e.message; })
        .finally(function () { genBtn.disabled = false; });
    });
  }
})();
