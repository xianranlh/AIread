/* 讲解页/笔记库页共用：选中文字 → 翻译 / 批注；右键单词 → 翻译；右键批注 → 编辑/删除。
   配置读自 #doc-main 的 data 属性：data-annot-base（如 /item/123）、data-admin-user。
   依赖页面存在元素：#doc-main #notes-rail #sel-menu #trans-popup #annot-editor #annot-text #annot-quote */
(function () {
  var main = document.getElementById("doc-main");
  if (!main) return;
  var rail = document.getElementById("notes-rail");
  var menu = document.getElementById("sel-menu");
  var editor = document.getElementById("annot-editor");
  var editorText = document.getElementById("annot-text");
  var editorQuote = document.getElementById("annot-quote");
  var popup = document.getElementById("trans-popup");
  var ITEM = main.dataset.annotBase;                 // 批注接口基址 /item/123
  var ADMIN_USER = main.dataset.adminUser || "admin";
  var NOTE_ID = main.dataset.noteId || "";           // 笔记库：当前文件 id；讲解页为空
  var pwd = "", ann = [], pending = null, editingId = null;

  // ---------- 翻译（专业名词，调用后端 LLM）----------
  function showPopup(x, y, text) {
    popup.textContent = text;
    popup.style.left = Math.max(8, Math.min(x, window.innerWidth - 340)) + "px";
    popup.style.top = (y + 8) + "px";
    popup.hidden = false;
  }
  function translate(text, x, y) {
    if (!auth()) return;
    showPopup(x, y, "翻译中…");
    fetch("/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    }).then(function (r) { return r.json(); })
      .then(function (d) { if (!d.ok) throw new Error(d.error || "翻译失败"); showPopup(x, y, d.text); })
      .catch(function (e) { showPopup(x, y, "✗ " + e.message); });
  }

  function auth() { return true; }  // 已全站免登录
  function authHeader() { return ""; }

  // ---------- 文本定位 ----------
  function textNodes() {
    var w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, null), out = [], n;
    while ((n = w.nextNode())) out.push(n);
    return out;
  }
  function absOffset(node, offset) {
    var nodes = textNodes(), total = 0;
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i] === node) return total + offset;
      total += nodes[i].textContent.length;
    }
    return -1;
  }
  function occurrenceOf(quote, absStart) {
    var hay = main.textContent, c = 0, idx = hay.indexOf(quote);
    while (idx !== -1 && idx < absStart) { c++; idx = hay.indexOf(quote, idx + 1); }
    return c;
  }
  function highlight(a) {
    var hay = main.textContent, idx = hay.indexOf(a.quote), c = 0;
    while (idx !== -1 && c < a.occurrence) { idx = hay.indexOf(a.quote, idx + 1); c++; }
    if (idx === -1) return false;
    var end = idx + a.quote.length, nodes = textNodes(), pos = 0;
    var sN = null, sO = 0, eN = null, eO = 0;
    for (var i = 0; i < nodes.length; i++) {
      var len = nodes[i].textContent.length;
      if (sN === null && idx < pos + len) { sN = nodes[i]; sO = idx - pos; }
      if (sN !== null && end <= pos + len) { eN = nodes[i]; eO = end - pos; break; }
      pos += len;
    }
    if (!sN || !eN) return false;
    var range = document.createRange();
    range.setStart(sN, sO); range.setEnd(eN, eO);
    var mark = document.createElement("mark");
    mark.className = "annot"; mark.dataset.id = a.id;
    try { range.surroundContents(mark); return true; }
    catch (e) {
      var anchor = document.createElement("span");
      anchor.className = "annot-anchor"; anchor.dataset.id = a.id;
      var r2 = document.createRange(); r2.setStart(sN, sO); r2.collapse(true);
      try { r2.insertNode(anchor); } catch (e2) { return false; }
      return true;
    }
  }

  function layoutNotes() {
    var narrow = window.innerWidth < 1300;
    var cards = Array.prototype.slice.call(rail.children);
    if (narrow) { rail.style.height = "auto"; cards.forEach(function (c) { c.style.position = "static"; c.style.top = "auto"; }); return; }
    rail.style.height = main.offsetHeight + "px";
    var railTop = rail.getBoundingClientRect().top, last = 0;
    cards.forEach(function (card) {
      card.style.position = "absolute";
      var el = main.querySelector('[data-id="' + card.dataset.id + '"]');
      var top = el ? (el.getBoundingClientRect().top - railTop) : last + 8;
      if (top < last + 8) top = last + 8;
      card.style.top = top + "px";
      last = top + card.offsetHeight;
    });
  }

  function showMenu(x, y, buttons) {
    menu.innerHTML = "";
    buttons.forEach(function (b) {
      var el = document.createElement("button");
      el.textContent = b.label;
      el.addEventListener("mousedown", function (ev) { ev.preventDefault(); });
      el.addEventListener("click", function (ev) { ev.stopPropagation(); hideMenu(); b.fn(); });
      menu.appendChild(el);
    });
    menu.style.left = Math.min(x, window.innerWidth - 160) + "px";
    menu.style.top = y + "px";
    menu.hidden = false;
  }
  function hideMenu() { menu.hidden = true; }
  function selMenu(x, y, text, range) {
    showMenu(x, y, [
      { label: "🌐 翻译", fn: function () { translate(text, x, y); } },
      { label: "✏️ 批注", fn: function () { openCreate(text, range); } }
    ]);
  }

  main.addEventListener("mouseup", function () {
    setTimeout(function () {
      var sel = window.getSelection();
      if (!sel || sel.isCollapsed) return;
      var text = sel.toString().trim();
      if (!text || !main.contains(sel.anchorNode)) return;
      var rect = sel.getRangeAt(0).getBoundingClientRect();
      selMenu(rect.left, rect.bottom + 4, text, sel.getRangeAt(0));
    }, 0);
  });

  main.addEventListener("contextmenu", function (ev) {
    var mark = ev.target.closest && ev.target.closest("mark.annot");
    if (mark) {
      ev.preventDefault();
      var id = mark.dataset.id;
      showMenu(ev.clientX, ev.clientY, [
        { label: "🌐 翻译", fn: function () { translate(mark.textContent, ev.clientX, ev.clientY); } },
        { label: "✏️ 编辑批注", fn: function () { openEdit(id); } },
        { label: "🗑 删除批注", fn: function () { del(id); } }
      ]);
      return;
    }
    var sel = window.getSelection();
    var text = (sel && !sel.isCollapsed) ? sel.toString().trim() : "";
    var range = null;
    if (text) { range = sel.getRangeAt(0); }
    else { range = selectWordAtPoint(ev.clientX, ev.clientY); if (range) text = range.toString().trim(); }
    if (!text) return;
    ev.preventDefault();
    selMenu(ev.clientX, ev.clientY, text, range);
  });

  function selectWordAtPoint(x, y) {
    var pos = null;
    if (document.caretRangeFromPoint) pos = document.caretRangeFromPoint(x, y);
    else if (document.caretPositionFromPoint) { var p = document.caretPositionFromPoint(x, y); if (p) { pos = document.createRange(); pos.setStart(p.offsetNode, p.offset); } }
    if (!pos) return null;
    var node = pos.startContainer; if (node.nodeType !== 3) return null;
    var s = node.textContent, i = pos.startOffset;
    var isW = function (c) { return c && /[A-Za-z0-9'À-ɏ一-鿿_\-]/.test(c); };
    if (!isW(s[i]) && isW(s[i - 1])) i--;
    var a = i, b = i;
    while (a > 0 && isW(s[a - 1])) a--;
    while (b < s.length && isW(s[b])) b++;
    if (a === b) return null;
    var r = document.createRange(); r.setStart(node, a); r.setEnd(node, b);
    var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
    return r;
  }

  function showEditor(rect) {
    editor.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - 340)) + "px";
    editor.style.top = (rect.bottom + 6) + "px";
    editor.hidden = false;
  }
  function openCreate(text, range) {
    var abs = absOffset(range.startContainer, range.startOffset);
    pending = { quote: text, occurrence: occurrenceOf(text, abs) };
    editingId = null;
    editorQuote.textContent = "“" + (text.length > 36 ? text.slice(0, 36) + "…" : text) + "”";
    editorText.value = "";
    showEditor(range.getBoundingClientRect());
    editorText.focus();
  }
  function openEdit(id) {
    var a = ann.filter(function (x) { return String(x.id) === String(id); })[0];
    if (!a) return;
    pending = null; editingId = id;
    editorQuote.textContent = "“" + (a.quote.length > 36 ? a.quote.slice(0, 36) + "…" : a.quote) + "”";
    editorText.value = a.note;
    var el = main.querySelector('[data-id="' + id + '"]');
    showEditor(el ? el.getBoundingClientRect() : { left: 100, bottom: 120 });
    editorText.focus();
  }
  document.getElementById("annot-cancel").addEventListener("click", function () { editor.hidden = true; });
  document.getElementById("annot-save").addEventListener("click", function () {
    var note = editorText.value.trim(); if (!note) return;
    if (!auth()) return;
    var url, body;
    if (editingId) { url = ITEM + "/annotations/" + editingId; body = { note: note }; }
    else { url = ITEM + "/annotations"; body = { quote: pending.quote, occurrence: pending.occurrence, note: note, note_id: NOTE_ID || null }; }
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (!d.ok) throw new Error(d.error || "保存失败"); editor.hidden = true; reload(); })
      .catch(function (e) { alert("✗ " + e.message); });
  });

  function del(id) {
    if (!auth()) return;
    if (!window.confirm("删除这条批注？")) return;
    fetch(ITEM + "/annotations/" + id, { method: "DELETE", })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (!d.ok) throw new Error("删除失败"); reload(); })
      .catch(function (e) { alert("✗ " + e.message); });
  }

  function addCard(a) {
    var card = document.createElement("div");
    card.className = "note-card"; card.dataset.id = a.id;
    var body = document.createElement("div"); body.className = "note-body"; body.textContent = a.note;
    var acts = document.createElement("div"); acts.className = "note-actions";
    var be = document.createElement("button"); be.textContent = "编辑"; be.addEventListener("click", function () { openEdit(a.id); });
    var bd = document.createElement("button"); bd.textContent = "删除"; bd.addEventListener("click", function () { del(a.id); });
    acts.appendChild(be); acts.appendChild(bd);
    card.appendChild(body); card.appendChild(acts);
    card.addEventListener("mouseenter", function () { var m = main.querySelector('[data-id="' + a.id + '"]'); if (m) m.classList.add("annot-hover"); });
    card.addEventListener("mouseleave", function () { var m = main.querySelector('[data-id="' + a.id + '"]'); if (m) m.classList.remove("annot-hover"); });
    rail.appendChild(card);
  }

  function clearMarks() {
    main.querySelectorAll("mark.annot, span.annot-anchor").forEach(function (m) {
      var p = m.parentNode;
      while (m.firstChild) p.insertBefore(m.firstChild, m);
      p.removeChild(m); p.normalize();
    });
    rail.innerHTML = "";
  }
  function loadAnnotations() {
    var u = ITEM + "/annotations" + (NOTE_ID ? "?note_id=" + NOTE_ID : "");
    fetch(u).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) return;
      ann = d.annotations || [];
      ann.forEach(function (a) { highlight(a); addCard(a); });
      layoutNotes();
    });
  }
  function reload() { clearMarks(); loadAnnotations(); }

  document.addEventListener("click", function (ev) {
    if (!menu.contains(ev.target)) hideMenu();
    if (popup && !popup.contains(ev.target)) popup.hidden = true;
  });
  window.addEventListener("resize", layoutNotes);
  window.addEventListener("load", function () { setTimeout(layoutNotes, 50); });
  window.addEventListener("annot-reload", reload);   // AI 助手标注后刷新
  loadAnnotations();
})();
