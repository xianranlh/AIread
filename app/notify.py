"""每日推送：Telegram / 邮件（SMTP）。未配置则静默跳过；失败不影响管线。

手动测试：python -m app.notify --test   （发送测试消息到已配置渠道）
手动推送：python -m app.notify          （推送最近一天的摘要）
"""
import json
import logging
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText

from app.collectors.base import http_client
from app.config import get_settings
from app.db import db

log = logging.getLogger("notify")


def _digest(conn, run_date: str):
    """生成摘要，返回 (纯文本[TG用], HTML[邮件用])；无内容返回 None。"""
    s = get_settings()
    rows = conn.execute(
        """SELECT i.id, i.title, i.category, i.score, e.content FROM items i
           LEFT JOIN explanations e ON e.item_id = i.id
           WHERE i.run_date=? AND i.status IN ('selected','explained')
           ORDER BY (i.status='explained') DESC, i.score DESC LIMIT ?""",
        (run_date, s.notify_top_n),
    ).fetchall()
    if not rows:
        return None
    total = conn.execute(
        "SELECT COUNT(*) AS n FROM items WHERE run_date=? AND status IN ('selected','explained')",
        (run_date,),
    ).fetchone()["n"]
    t = [f"📡 {s.site_title} · {run_date}", f"今日精选 {total} 条，Top {len(rows)}：", ""]
    h = [f"<h2>📡 {s.site_title} · {run_date}</h2><p>今日精选 {total} 条，Top {len(rows)}：</p><ol>"]
    for r in rows:
        one = ""
        if r["content"]:
            try:
                one = json.loads(r["content"]).get("one_liner", "")
            except json.JSONDecodeError:
                pass
        url = f"{s.site_url}/item/{r['id']}"
        t.append(f"▪ [{r['category']}] {r['title']}")
        if one:
            t.append(f"  {one}")
        t.append(f"  {url}")
        h.append(f'<li style="margin-bottom:10px"><b>[{r["category"]}] {r["title"]}</b>'
                 f"<br>{one}<br>" + f'<a href="{url}">阅读讲解 →</a></li>')
    t.append(f"\n全部内容：{s.site_url}")
    h.append(f'</ol><p><a href="{s.site_url}">打开站点查看全部 →</a></p>')
    return "\n".join(t), "".join(h)


def send_telegram(text: str):
    """返回 True/False；未配置返回 None。"""
    s = get_settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        return None
    try:
        with http_client() as client:
            r = client.post(
                f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage",
                data={"chat_id": s.telegram_chat_id, "text": text[:4000],
                      "disable_web_page_preview": "true"},
            )
            ok = r.status_code == 200
            if not ok:
                log.warning("Telegram 推送失败: %s %s", r.status_code, r.text[:200])
            return ok
    except Exception:  # noqa: BLE001
        log.exception("Telegram 推送异常")
        return False


def send_email(subject: str, html: str):
    """返回 True/False；未配置返回 None。"""
    s = get_settings()
    if not (s.smtp_host and s.smtp_user and s.smtp_pass and s.mail_to):
        return None
    try:
        msg = MIMEText(html, "html", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = s.smtp_user
        to_list = [x.strip() for x in s.mail_to.split(",") if x.strip()]
        msg["To"] = ", ".join(to_list)
        if int(s.smtp_port) == 465:
            server = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=20)
        else:
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20)
            server.starttls()
        with server:
            server.login(s.smtp_user, s.smtp_pass)
            server.sendmail(s.smtp_user, to_list, msg.as_string())
        return True
    except Exception:  # noqa: BLE001
        log.exception("邮件推送异常")
        return False


def notify_daily(conn, run_date: str) -> dict:
    s = get_settings()
    tg_on = bool(s.telegram_bot_token and s.telegram_chat_id)
    mail_on = bool(s.smtp_host and s.smtp_user and s.smtp_pass and s.mail_to)
    if not (tg_on or mail_on):
        return {"skipped": "未配置推送渠道"}
    d = _digest(conn, run_date)
    if not d:
        return {"skipped": "当日无内容"}
    text, html = d
    out = {}
    if tg_on:
        out["telegram"] = send_telegram(text)
    if mail_on:
        out["email"] = send_email(f"{s.site_title} · {run_date} 精选", html)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if "--test" in sys.argv:
        print("telegram:", send_telegram("📡 AI 技术雷达：推送测试消息，配置成功！"))
        print("email:", send_email("AI 技术雷达 · 推送测试", "<p>推送测试成功！</p>"))
    else:
        with db() as conn:
            row = conn.execute("SELECT MAX(run_date) AS d FROM items").fetchone()
            if row and row["d"]:
                print(notify_daily(conn, row["d"]))
            else:
                print("无数据")
