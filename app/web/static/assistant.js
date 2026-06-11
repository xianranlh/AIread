/* 浮动 AI 笔记助手：可拖动按钮 + 对话面板（多轮）+ 回复可标注到文章/生成笔记 */
(function () {
  "use strict";
  var fab = document.getElementById("ai-fab");
  var panel = document.getElementById("ai-panel");
  if (!fab || !panel) { return; }
  var modelSel = document.getElementById("ai-model");
  var ctxBox = document.getElementById("ai-ctx");
  var chatBox = document.getElementById("ai-chat");
  var instr = document.getElementById("ai-instr");
  var sendBtn = document.getElementById("ai-send");
  var genBtn = document.getElementById("ai-gen");
  var status = document.getElementById("ai-status");
  var exportRow = document.getElementById("ai-export");
  var tabChat = document.getElementById("ai-tab-chat");
  var tabNote = document.getElementById("ai-tab-note");
  var viewChat = document.getElementById("ai-view-chat");
  var viewNote = document.getElementById("ai-view-note");
  var noteInstr = document.getElementById("ai-note-instr");
  var withChat = document.getElementById("ai-with-chat");
  var chatEmpty = document.getElementById("ai-chat-empty");
  var result = document.getElementById("ai-result");

  /* ---- Tab 切换：对话 / 笔记 ---- */
  function switchTab(name) {
    var isChat = name === "chat";
    viewChat.hidden = !isChat;
    viewNote.hidden = isChat;
    tabChat.classList.toggle("ai-tab-active", isChat);
    tabNote.classList.toggle("ai-tab-active", !isChat);
    try { localStorage.setItem("radar-panel-tab", name); } catch (e) {}
    if (isChat) { instr.focus(); }
  }
  tabChat.addEventListener("click", function () { switchTab("chat"); });
  tabNote.addEventListener("click", function () { switchTab("note"); });
  var lastSelection = "";
  var lastMd = "";
  var lastTitle = "note";
  var modelsLoaded = false;
  var history = [];          // [{role:'user'|'assistant', content: md}]

  /* ---- 按钮位置：恢复 + 约束在视口内 ---- */
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
  function restorePos() {
    try {
      var pos = JSON.parse(localStorage.getItem("radar-fab-pos") || "null");
      if (pos) {
        fab.style.left = clamp(pos.x, 0, window.innerWidth - 56) + "px";
        fab.style.top = clamp(pos.y, 0, window.innerHeight - 56) + "px";
        fab.style.right = "auto"; fab.style.bottom = "auto";
      }
    } catch (e) { /* ignore */ }
  }
  restorePos();

  /* ---- 拖动（pointer events），移动 < 6px 视为点击 ---- */
  var drag = null;
  fab.addEventListener("pointerdown", function (e) {
    if (e.button !== 0) { return; }
    lastSelection = getSelText();           // 在焦点转移前抓选区
    var r = fab.getBoundingClientRect();
    drag = { sx: e.clientX, sy: e.clientY, ox: r.left, oy: r.top, moved: false };
    fab.setPointerCapture(e.pointerId);
  });
  fab.addEventListener("pointermove", function (e) {
    if (!drag) { return; }
    var dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
    if (Math.abs(dx) + Math.abs(dy) > 6) { drag.moved = true; }
    if (drag.moved) {
      fab.style.left = clamp(drag.ox + dx, 0, window.innerWidth - 56) + "px";
      fab.style.top = clamp(drag.oy + dy, 0, window.innerHeight - 56) + "px";
      fab.style.right = "auto"; fab.style.bottom = "auto";
    }
  });
  fab.addEventListener("pointerup", function () {
    if (!drag) { return; }
    if (drag.moved) {
      var r = fab.getBoundingClientRect();
      try { localStorage.setItem("radar-fab-pos", JSON.stringify({x: r.left, y: r.top})); } catch (e) {}
    } else {
      togglePanel();
    }
    drag = null;
  });
  fab.addEventListener("contextmenu", function (e) {   // 右键：带当前选中内容打开
    e.preventDefault();
    lastSelection = getSelText();
    openPanel();
  });

  function getSelText() {
    var s = window.getSelection ? String(window.getSelection()) : "";
    return s.trim().slice(0, 8000);
  }

  /* ---- 面板 ---- */
  function pageCtx() {
    var m = window.location.pathname.match(/^\/(?:item|library)\/(\d+)/);
    var note = new URLSearchParams(window.location.search).get("note");
    return {
      title: document.title,
      url: window.location.href,
      item_id: m ? parseInt(m[1], 10) : null,
      note_id: note ? parseInt(note, 10) : null
    };
  }
  function renderCtx() {
    var c = pageCtx();
    var html = "<b>已抓取上下文</b><br>页面：" + escapeHtml(c.title);
    if (c.item_id) { html += "<br>条目 #" + c.item_id + "（将自动附带讲解与材料）"; }
    html += "<br>选中内容：" + (lastSelection
      ? escapeHtml(lastSelection.slice(0, 120)) + (lastSelection.length > 120 ? "…" : "") + "（" + lastSelection.length + " 字）"
      : "<i>无（可先选中页面文字再右键本按钮）</i>");
    ctxBox.innerHTML = html;
  }
  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function togglePanel() { if (panel.hidden) { openPanel(); } else { panel.hidden = true; } }
  function openPanel() {
    panel.hidden = false;
    renderCtx();
    placePanel();
    if (!modelsLoaded) { loadModels(); }
    var t = "chat";
    try { t = localStorage.getItem("radar-panel-tab") || "chat"; } catch (e) {}
    switchTab(t);
  }
  function placePanel() {
    var r = fab.getBoundingClientRect();
    var saved = null;
    try { saved = JSON.parse(localStorage.getItem("radar-panel-size2") || "null"); } catch (e) {}
    var pw = clamp(saved && saved.w || 520, 340, window.innerWidth - 24);
    var ph = clamp(saved && saved.h || 640, 360, window.innerHeight - 30);
    panel.style.width = pw + "px";
    panel.style.height = ph + "px";
    var left = clamp(r.left - pw + 56, 12, window.innerWidth - pw - 12);
    panel.style.left = left + "px";
    var top = (r.top > window.innerHeight / 2) ? r.top - ph - 10 : r.bottom + 10;
    panel.style.top = clamp(top, 10, window.innerHeight - ph - 10) + "px";
    panel.style.bottom = "auto";
  }
  /* ---- 四边/四角拖拽调整面板大小 ---- */
  (function () {
    var MIN_W = 340, MIN_H = 360;
    panel.querySelectorAll(".ai-rz").forEach(function (h) {
      h.addEventListener("pointerdown", function (e) {
        e.preventDefault(); e.stopPropagation();
        var dir = h.dataset.rz;
        var r = panel.getBoundingClientRect();
        var sx = e.clientX, sy = e.clientY;
        var start = { left: r.left, top: r.top, w: r.width, h: r.height };
        h.setPointerCapture(e.pointerId);
        function onMove(ev) {
          var dx = ev.clientX - sx, dy = ev.clientY - sy;
          var L = start.left, T = start.top, W = start.w, H = start.h;
          if (dir.indexOf("r") !== -1) { W = start.w + dx; }
          if (dir.indexOf("l") !== -1) { W = start.w - dx; L = start.left + dx; }
          if (dir.indexOf("b") !== -1) { H = start.h + dy; }
          if (dir.indexOf("t") !== -1) { H = start.h - dy; T = start.top + dy; }
          // 最小/视口约束（拖左/上边时尺寸到下限后停住，不再移动位置）
          if (W < MIN_W) { if (dir.indexOf("l") !== -1) { L -= (MIN_W - W); } W = MIN_W; }
          if (H < MIN_H) { if (dir.indexOf("t") !== -1) { T -= (MIN_H - H); } H = MIN_H; }
          W = Math.min(W, window.innerWidth - 16);
          H = Math.min(H, window.innerHeight - 16);
          L = clamp(L, 4, window.innerWidth - 60);
          T = clamp(T, 4, window.innerHeight - 60);
          panel.style.width = W + "px"; panel.style.height = H + "px";
          panel.style.left = L + "px"; panel.style.top = T + "px";
          panel.style.bottom = "auto";
        }
        function onUp(ev) {
          h.removeEventListener("pointermove", onMove);
          h.removeEventListener("pointerup", onUp);
          try {
            localStorage.setItem("radar-panel-size2",
              JSON.stringify({ w: panel.offsetWidth, h: panel.offsetHeight }));
          } catch (err) {}
        }
        h.addEventListener("pointermove", onMove);
        h.addEventListener("pointerup", onUp);
      });
    });
  })();
  /* ---- 阻止面板上的滚轮带动页面（滚动链穿透） ---- */
  panel.addEventListener("wheel", function (e) {
    var el = e.target;
    while (el && el !== panel) {
      if (el.scrollHeight > el.clientHeight + 1) {
        var canUp = e.deltaY < 0 && el.scrollTop > 0;
        var canDown = e.deltaY > 0 && el.scrollTop + el.clientHeight < el.scrollHeight - 1;
        if (canUp || canDown) { return; }   // 面板内部还能滚，正常放行
      }
      el = el.parentElement;
    }
    e.preventDefault();                     // 内部滚不动了：拦截，别传给页面
  }, { passive: false });

  document.getElementById("ai-close").addEventListener("click", function () { panel.hidden = true; });
  document.getElementById("ai-clear").addEventListener("click", function () {
    history = [];
    chatBox.innerHTML = "";
    if (chatEmpty) { chatBox.appendChild(chatEmpty); }
    status.textContent = "对话已清空";
  });

  function loadModels() {
    fetch("/api/models").then(function (r) { return r.json(); }).then(function (d) {
      modelSel.innerHTML = "";
      (d.models || []).forEach(function (m) {
        var opt = document.createElement("option");
        opt.value = m.role;
        opt.textContent = m.label + " · " + m.model;
        modelSel.appendChild(opt);
      });
      try {
        var saved = localStorage.getItem("radar-note-role");
        if (saved) { modelSel.value = saved; }
      } catch (e) {}
      modelsLoaded = true;
    }).catch(function () { status.textContent = "模型列表加载失败"; });
  }
  modelSel.addEventListener("change", function () {
    try { localStorage.setItem("radar-note-role", modelSel.value); } catch (e) {}
  });

  /* ---- 对话 ---- */
  function addBubble(role, html, md) {
    if (chatEmpty && chatEmpty.parentNode) { chatEmpty.remove(); }
    var b = document.createElement("div");
    b.className = "ai-msg ai-msg-" + role;
    var body = document.createElement("div");
    body.className = "ai-msg-body" + (role === "assistant" ? " prose" : "");
    if (role === "assistant") { body.innerHTML = html; } else { body.textContent = md; }
    b.appendChild(body);
    if (role === "assistant") {
      var acts = document.createElement("div");
      acts.className = "ai-msg-acts";
      var c = pageCtx();
      if (c.item_id) {
        var ab = document.createElement("button");
        ab.textContent = "📌 标注到原文";
        ab.title = "先在文章里选中要标注的文字，再点这里，把这条回复挂为该处批注";
        ab.addEventListener("click", function () { annotate(md, ab); });
        acts.appendChild(ab);
      }
      var cp = document.createElement("button");
      cp.textContent = "复制";
      cp.addEventListener("click", function () {
        navigator.clipboard.writeText(md).then(function () { cp.textContent = "已复制✓"; });
      });
      acts.appendChild(cp);
      b.appendChild(acts);
    }
    chatBox.appendChild(b);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function sendMsg() {
    var msg = instr.value.trim();
    if (!msg) { return; }
    instr.value = "";
    addBubble("user", null, msg);
    history.push({ role: "user", content: msg });
    status.textContent = "思考中…";
    sendBtn.disabled = true;
    fetch("/api/assistant/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: modelSel.value || "explainer",
        page: pageCtx(),
        selection: lastSelection,
        history: history.slice(0, -1),
        message: msg
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok) {
        history.push({ role: "assistant", content: d.markdown });
        addBubble("assistant", d.html, d.markdown);
        status.textContent = d.model;
      } else {
        status.textContent = "✗ " + (d.error || "未知错误");
      }
    }).catch(function (e) {
      status.textContent = "✗ " + e.message;
    }).finally(function () { sendBtn.disabled = false; instr.focus(); });
  }
  sendBtn.addEventListener("click", sendMsg);
  instr.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); sendMsg(); }
  });

  /* ---- 标注到原文：以「当前/最近选中的文字」为锚点，把回复挂为批注 ---- */
  function occurrenceOf(quote) {
    var main = document.getElementById("doc-main");
    if (!main) { return 0; }
    var sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { return 0; }
    try {
      var r = sel.getRangeAt(0);
      var pre = r.cloneRange();
      pre.selectNodeContents(main);
      pre.setEnd(r.startContainer, r.startOffset);
      var before = pre.toString();
      var c = 0, idx = before.indexOf(quote);
      while (idx !== -1) { c++; idx = before.indexOf(quote, idx + 1); }
      return c;
    } catch (e) { return 0; }
  }
  function annotate(md, btn) {
    var c = pageCtx();
    var quote = getSelText() || lastSelection;
    if (!quote) {
      status.textContent = "请先在文章里选中要标注的位置的文字，再点「标注到原文」";
      return;
    }
    var occ = occurrenceOf(quote);
    btn.disabled = true;
    fetch("/item/" + c.item_id + "/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quote: quote, occurrence: occ, note: md, note_id: c.note_id })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok) {
        btn.textContent = "已标注✓";
        status.textContent = "已标注到原文（右侧批注栏可见）";
        window.dispatchEvent(new CustomEvent("annot-reload"));
      } else {
        btn.disabled = false;
        status.textContent = "✗ 标注失败";
      }
    }).catch(function (e) { btn.disabled = false; status.textContent = "✗ " + e.message; });
  }

  /* ---- 生成结构化笔记（保存到「我的笔记」）---- */
  genBtn.addEventListener("click", function () {
    status.textContent = "生成中…（约 10-40 秒）";
    genBtn.disabled = true;
    exportRow.hidden = true;
    var instruction = noteInstr.value.trim();
    if (history.length && withChat.checked) {
      var talk = history.map(function (h) {
        return (h.role === "user" ? "用户" : "助手") + "：" + h.content;
      }).join("\n\n").slice(0, 6000);
      instruction = (instruction ? instruction + "\n\n" : "") + "请把以下对话中的要点整理进笔记：\n" + talk;
    }
    fetch("/api/note", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: modelSel.value || "explainer",
        page: pageCtx(),
        selection: lastSelection,
        instruction: instruction
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok) {
        lastMd = d.markdown; lastTitle = d.title || "note";
        result.innerHTML = d.html;
        exportRow.hidden = false;
        status.textContent = "已生成并保存到「我的笔记」（" + d.model + "）";
      } else {
        status.textContent = "✗ " + (d.error || "未知错误");
      }
    }).catch(function (e) {
      status.textContent = "✗ " + e.message;
    }).finally(function () { genBtn.disabled = false; });
  });

  /* ---- 导出 ---- */
  document.getElementById("ai-copy").addEventListener("click", function () {
    navigator.clipboard.writeText(lastMd).then(function () {
      status.textContent = "已复制 Markdown";
    }, function () { status.textContent = "复制失败，请手动选择"; });
  });
  document.getElementById("ai-dl").addEventListener("click", function () {
    var blob = new Blob([lastMd], {type: "text/markdown;charset=utf-8"});
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = lastTitle.replace(/[\\/:*?"<>|]/g, "_").slice(0, 60) + ".md";
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  });
})();
