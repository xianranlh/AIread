"""把本地知识文件夹导入为「笔记库」条目（note_files），图片拷到数据卷 /data/lib-assets。
幂等：按 external_id 覆盖。直接在宿主机对 ./data/radar.db 运行。"""
import hashlib
import posixpath
import re
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path

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


def rewrite(text: str, md_dir: str, slug: str) -> str:
    def fix(url: str) -> str:
        if url.startswith(("http://", "https://", "/lib-assets/", "data:", "//")):
            return url
        joined = posixpath.normpath(posixpath.join(md_dir, url)).lstrip("/")
        return f"/lib-assets/{slug}/{joined}"
    text = MD_IMG.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), text)
    text = HTML_IMG.sub(lambda m: m.group(1) + fix(m.group(2)) + m.group(3), text)
    return text


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
    # 4) note_files
    for i, p in enumerate(mds):
        rel = p.relative_to(root).as_posix()
        md_dir = posixpath.dirname(rel)
        content = rewrite(p.read_text(encoding="utf-8", errors="replace"), md_dir, slug)
        conn.execute("INSERT INTO note_files(item_id, path, ord, content) VALUES (?,?,?,?)",
                     (item_id, rel, i, content))
    conn.commit()
    print(f"✓ {title}: {len(mds)} 篇 md, {n_img} 张图 -> item #{item_id}")
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
