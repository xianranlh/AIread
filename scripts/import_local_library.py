"""把本地知识文件夹导入为「笔记库」条目（note_files），图片拷到数据卷 /data/lib-assets。
幂等：按 external_id 覆盖。直接在宿主机对 ./data/radar.db 运行。"""
import hashlib
import posixpath
import re
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

SRC_ROOT = Path("/root/JavaGuide-2026年3月24日")
DB = Path("/root/AIread/data/radar.db")
ASSETS = Path("/root/AIread/data/lib-assets")

# (子文件夹名, slug, 展示标题, 链接)
BUNDLES = [
    ("《Java面试指北》", "java-interview-guide", "《Java 面试指北》", "https://javaguide.cn/"),
    ("SpringAI智能面试平台+RAG知识库", "springai-rag",
     "SpringAI 智能面试平台 + RAG 知识库", "https://javaguide.cn/"),
]

now = lambda: datetime.now().isoformat(timespec="seconds")  # noqa: E731
sha1 = lambda s: hashlib.sha1(s.encode()).hexdigest()       # noqa: E731

# markdown ![](url) 与 HTML <img src="url">
MD_IMG = re.compile(r'(!\[[^\]]*\]\()\s*([^)\s]+)([^)]*\))')
HTML_IMG = re.compile(r'(<img[^>]*\bsrc=")([^"]+)(")', re.I)
MD_LINK = re.compile(r'(\]\()([^)]+)(\))')  # 链接（图片已先转成 /lib-assets 不会命中）


def rewrite_images(text: str, md_dir: str, slug: str) -> str:
    def fix(url: str) -> str:
        if url.startswith(("http://", "https://", "/lib-assets/", "data:", "//")):
            return url
        joined = posixpath.normpath(posixpath.join(md_dir, url)).lstrip("/")
        return f"/lib-assets/{slug}/{joined}"
    text = MD_IMG.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), text)
    text = HTML_IMG.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), text)
    return text


def rewrite_links(text: str, md_dir: str, item_id: int, path2note: dict) -> str:
    """库内 md→md 相对链接改写成 /library/{item}?note={id}。"""
    def fix(m):
        raw = m.group(2).strip()
        if raw.startswith(("http://", "https://", "/", "#", "mailto:")):
            return m.group(0)
        base, sep, anchor = raw.partition("#")
        if not base.lower().endswith(".md"):
            return m.group(0)
        target = posixpath.normpath(posixpath.join(md_dir, unquote(base))).lstrip("/")
        nid = path2note.get(target)
        if nid is None:  # 容错：按结尾匹配唯一项
            cand = [p for p in path2note if p.endswith(target) or p.endswith(unquote(base))]
            nid = path2note[cand[0]] if len(cand) == 1 else None
        if nid is None:
            return m.group(0)
        return f"{m.group(1)}/library/{item_id}?note={nid}{m.group(3)}"
    return MD_LINK.sub(fix, text)


def import_bundle(conn, folder, slug, title, url):
    root = SRC_ROOT / folder
    if not root.is_dir():
        print(f"跳过（不存在）：{folder}")
        return
    # 1) 拷贝图片资源（任何位于 img 目录下的文件），保留相对路径
    dest = ASSETS / slug
    if dest.exists():
        shutil.rmtree(dest)
    n_img = 0
    for f in root.rglob("*"):
        if f.is_file() and "img" in f.relative_to(root).parts:
            tgt = dest / f.relative_to(root)
            tgt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, tgt)
            n_img += 1
    # 2) 收集 md
    mds = sorted([p for p in root.rglob("*.md")],
                 key=lambda p: str(p.relative_to(root)).lower())
    # 3) items 行（覆盖式）
    canon = f"local://javaguide/{slug}"
    ext = sha1(canon)
    metrics = f'{{"library": true, "file_count": {len(mds)}}}'
    summary = "本地导入的知识库（JavaGuide 配套小册）"
    row = conn.execute("SELECT id FROM items WHERE external_id=?", (ext,)).fetchone()
    if row:
        item_id = row[0]
        conn.execute("UPDATE items SET source='library', title=?, url=?, summary=?, "
                     "metrics=?, status='library' WHERE id=?",
                     (title, url, summary, metrics, item_id))
        conn.execute("DELETE FROM note_files WHERE item_id=?", (item_id,))
    else:
        item_id = conn.execute(
            """INSERT INTO items(external_id, source, title, url, summary, metrics,
                                 status, run_date, fetched_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (ext, "library", title, url, summary, metrics, "library",
             date.today().isoformat(), now())).lastrowid
    # 4) note_files —— Pass1：先写入（图片已重写），建立 path→note_id 映射
    path2note: dict[str, int] = {}
    rows = []  # (note_id, rel, md_dir)
    for i, p in enumerate(mds):
        rel = p.relative_to(root).as_posix()
        md_dir = posixpath.dirname(rel)
        content = rewrite_images(p.read_text(encoding="utf-8", errors="replace"), md_dir, slug)
        nid = conn.execute(
            "INSERT INTO note_files(item_id, path, ord, content) VALUES (?,?,?,?)",
            (item_id, rel, i, content)).lastrowid
        path2note[rel] = nid
        rows.append((nid, rel, md_dir))
    # Pass2：把库内 md→md 链接改写成 /library/{item}?note={id}
    n_link = 0
    for nid, rel, md_dir in rows:
        cur = conn.execute("SELECT content FROM note_files WHERE id=?", (nid,)).fetchone()[0]
        new = rewrite_links(cur, md_dir, item_id, path2note)
        if new != cur:
            conn.execute("UPDATE note_files SET content=? WHERE id=?", (new, nid))
            n_link += 1
    conn.commit()
    print(f"✓ {title}: {len(mds)} 篇 md, {n_img} 张图, {n_link} 篇含内链已改写 -> item #{item_id}")
    return item_id


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        for folder, slug, title, url in BUNDLES:
            import_bundle(conn, folder, slug, title, url)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
