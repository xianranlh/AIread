/* 浮动 AI 笔记助手：可拖动按钮 + 笔记面板 */
(function () {
  "use strict";
  var fab = document.getElementById("ai-fab");
  var panel = document.getElementById("ai-panel");
  if (!fab || !panel) { return; }
  var modelSel = document.getElementById("ai-model");
  var ctxBox = document.getElementById("ai-ctx");
  var instr = document.getElementById("ai-instr");
  var genBtn = document.getElementById("ai-gen");
  var status = document.getElementById("ai-status");
  var result = document.getElementById("ai-result");
  var exportRow = document.getElementById("ai-export");
  var lastSelection = "";
  var lastMd = "";
  var lastTitle = "note";
  var modelsLoaded = false;

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
    var m = window.location.pathname.match(/^\/item\/(\d+)/);
    return {
      title: document.title,
      url: window.location.href,
      item_id: m ? parseInt(m[1], 10) : null
    };
  }
  function renderCtx() {
    var c = pageCtx();
    var html = "<b>已抓取上下文</b><br>页面：" + escapeHtml(c.title);
    if (c.item_id) { html += "<br>条目 #" + c.item_id + "（将自动附带讲解与 README 材料）"; }
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
  }
  function placePanel() {
    var r = fab.getBoundingClientRect();
    var pw = Math.min(380, window.innerWidth - 24);
    var left = clamp(r.left - pw + 56, 12, window.innerWidth - pw - 12);
    panel.style.width = pw + "px";
    panel.style.left = left + "px";
    if (r.top > window.innerHeight / 2) {
      panel.style.bottom = (window.innerHeight - r.top + 10) + "px"; panel.style.top = "auto";
    } else {
      panel.style.top = (r.bottom + 10) + "px"; panel.style.bottom = "auto";
    }
  }
  document.getElementById("ai-close").addEventListener("click", function () { panel.hidden = true; });

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

  /* ---- 生成 ---- */
  function getPwd() {
    var p = "";
    try { p = sessionStorage.getItem("radar-pwd") || ""; } catch (e) {}
    if (!p) {
      p = window.prompt("管理密码（用户名 admin）") || "";
      if (p) { try { sessionStorage.setItem("radar-pwd", p); } catch (e) {} }
    }
    return p;
  }
  genBtn.addEventListener("click", function () {
    var pwd = getPwd();
    if (!pwd) { return; }
    status.textContent = "生成中…（约 10-40 秒）";
    genBtn.disabled = true;
    result.innerHTML = "";
    exportRow.hidden = true;
    fetch("/api/note", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Basic " + btoa("admin:" + pwd)
      },
      body: JSON.stringify({
        role: modelSel.value || "explainer",
        page: pageCtx(),
        selection: lastSelection,
        instruction: instr.value.trim()
      })
    }).then(function (r) {
      if (r.status === 401) {
        try { sessionStorage.removeItem("radar-pwd"); } catch (e) {}
        throw new Error("密码错误，请重试");
      }
      return r.json();
    }).then(function (d) {
      if (d.ok) {
        lastMd = d.markdown; lastTitle = d.title || "note";
        result.innerHTML = d.html;
        exportRow.hidden = false;
        status.textContent = "已生成并保存（" + d.model + "）";
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
