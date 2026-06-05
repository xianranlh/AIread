"""FSRS-5 间隔重复调度器——对齐 ts-fsrs 的默认参数、卡片状态机与遗忘曲线。

状态机（与 ts-fsrs 一致）：
  New --Again/Hard/Good--> Learning（分钟级短间隔）   New --Easy--> Review
  Learning/Relearning --Good/Easy--> Review（天级间隔）  --Again/Hard--> 原状态
  Review --Again--> Relearning（lapses+1）  --Hard/Good/Easy--> Review

遗忘曲线（艾宾浩斯）： R(t) = (1 + FACTOR·t/S)^DECAY ，S 为稳定度，
当 t=S 时 R=90%，间隔按目标保留率 90% 反推，记忆越稳间隔越长。
"""
import math
from datetime import datetime, timedelta

# ts-fsrs / FSRS-5 默认权重 w0..w18
W = [0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046,
     1.54575, 0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315,
     2.9898, 0.51655, 0.6621]
DECAY = -0.5
FACTOR = 19 / 81            # 使 R(S)=0.9
REQUEST_RETENTION = 0.9     # 目标记忆保留率
MAX_INTERVAL = 36500

NEW, LEARNING, REVIEW, RELEARNING = 0, 1, 2, 3
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4
STATE_NAMES = {NEW: "新题", LEARNING: "学习中", REVIEW: "复习", RELEARNING: "重学"}
RATING_NAMES = {AGAIN: "忘了", HARD: "困难", GOOD: "记得", EASY: "简单"}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def init_stability(g: int) -> float:
    return max(W[g - 1], 0.1)


def init_difficulty(g: int) -> float:
    return _clamp(W[4] - math.exp(W[5] * (g - 1)) + 1, 1, 10)


def retrievability(elapsed_days: float, stability: float) -> float:
    """遗忘曲线：经过 t 天后的记忆保留率。"""
    if stability <= 0:
        return 0.0
    return (1 + FACTOR * max(0.0, elapsed_days) / stability) ** DECAY


def next_interval(stability: float) -> int:
    iv = stability / FACTOR * (REQUEST_RETENTION ** (1 / DECAY) - 1)
    return int(_clamp(round(iv), 1, MAX_INTERVAL))


def next_difficulty(d: float, g: int) -> float:
    delta = -W[6] * (g - 3)
    dp = d + delta * (10 - d) / 9          # 线性阻尼
    mean_rev = W[7] * init_difficulty(4) + (1 - W[7]) * dp   # 均值回归
    return _clamp(mean_rev, 1, 10)


def stability_recall(d: float, s: float, r: float, g: int) -> float:
    hard_penalty = W[15] if g == HARD else 1.0
    easy_bonus = W[16] if g == EASY else 1.0
    return s * (1 + math.exp(W[8]) * (11 - d) * s ** (-W[9])
                * (math.exp(W[10] * (1 - r)) - 1) * hard_penalty * easy_bonus)


def stability_forget(d: float, s: float, r: float) -> float:
    return min(W[11] * d ** (-W[12]) * ((s + 1) ** W[13] - 1)
               * math.exp(W[14] * (1 - r)), s)


def stability_short_term(s: float, g: int) -> float:
    """FSRS-5 短期（同日/学习阶段）记忆公式。"""
    return s * math.exp(W[17] * (g - 3 + W[18]))


def rate(card: dict, rating: int, now: datetime | None = None) -> dict:
    """对卡片打分（1忘了/2困难/3记得/4简单），返回更新后的卡片字段。

    card 需含: state, stability, difficulty, due, last_review, reps, lapses
    """
    assert rating in (AGAIN, HARD, GOOD, EASY)
    now = now or datetime.now()
    c = dict(card)
    state = c.get("state") or NEW
    orig_s = float(c.get("stability") or 0)
    orig_d = float(c.get("difficulty") or 0)
    last = c.get("last_review")
    elapsed = 0.0
    if last:
        elapsed = max(0.0, (now - datetime.fromisoformat(last)).total_seconds() / 86400)

    iv_days = 0
    if state == NEW:
        d, s = init_difficulty(rating), init_stability(rating)
        if rating == EASY:
            state = REVIEW
            iv_days = next_interval(s)
            due = now + timedelta(days=iv_days)
        else:
            state = LEARNING
            due = now + timedelta(minutes={AGAIN: 1, HARD: 5, GOOD: 10}[rating])
    elif state in (LEARNING, RELEARNING):
        d = next_difficulty(orig_d or init_difficulty(rating), rating)
        s = max(stability_short_term(orig_s or init_stability(rating), rating), 0.1)
        if rating in (GOOD, EASY):
            state = REVIEW
            iv_days = next_interval(s)
            due = now + timedelta(days=iv_days)
        else:
            due = now + timedelta(minutes=5 if rating == AGAIN else 10)
    else:  # REVIEW
        r = retrievability(elapsed, orig_s)
        d = next_difficulty(orig_d, rating)
        if rating == AGAIN:
            c["lapses"] = int(c.get("lapses") or 0) + 1
            s = max(stability_forget(orig_d, orig_s, r), 0.1)
            state = RELEARNING
            due = now + timedelta(minutes=5)
        else:
            s = stability_recall(orig_d, orig_s, r, rating)
            state = REVIEW
            iv_days = next_interval(s)
            due = now + timedelta(days=iv_days)

    c.update(
        state=state,
        stability=round(s, 4),
        difficulty=round(d, 4),
        last_review=now.isoformat(timespec="seconds"),
        due=due.isoformat(timespec="seconds"),
        reps=int(c.get("reps") or 0) + 1,
        scheduled_days=iv_days,
        elapsed_days=round(elapsed, 3),
    )
    return c


def preview(card: dict, now: datetime | None = None) -> dict:
    """4 个评分各自的下次间隔（人类可读），用于评分按钮标注。"""
    now = now or datetime.now()
    out = {}
    for g in (AGAIN, HARD, GOOD, EASY):
        nc = rate(card, g, now)
        delta = datetime.fromisoformat(nc["due"]) - now
        mins = delta.total_seconds() / 60
        if mins < 60:
            out[g] = f"{max(1, round(mins))}分"
        elif mins < 60 * 36:
            out[g] = f"{round(mins / 60)}小时"
        else:
            days = delta.days
            out[g] = f"{days}天" if days < 365 else f"{days / 365:.1f}年"
    return out


def card_retrievability(card: dict, now: datetime | None = None) -> float | None:
    """卡片当前记忆保持率（New 卡返回 None）。"""
    if (card.get("state") or NEW) == NEW or not card.get("last_review"):
        return None
    now = now or datetime.now()
    elapsed = (now - datetime.fromisoformat(card["last_review"])).total_seconds() / 86400
    return retrievability(elapsed, float(card.get("stability") or 0.1))


if __name__ == "__main__":
    # 自检：状态转移与间隔单调性
    from datetime import datetime as dt
    c = {"state": NEW, "stability": 0, "difficulty": 0, "due": None,
         "last_review": None, "reps": 0, "lapses": 0}
    t0 = dt(2026, 6, 1, 9, 0, 0)
    c1 = rate(c, GOOD, t0)
    assert c1["state"] == LEARNING and c1["scheduled_days"] == 0
    c2 = rate(c1, GOOD, t0 + timedelta(minutes=10))
    assert c2["state"] == REVIEW and c2["scheduled_days"] >= 1
    c3 = rate(c2, AGAIN, dt.fromisoformat(c2["due"]))
    assert c3["state"] == RELEARNING and c3["lapses"] == 1
    c4 = rate(c3, GOOD, dt.fromisoformat(c3["due"]))
    assert c4["state"] == REVIEW
    pv = preview(c2, dt.fromisoformat(c2["due"]))
    assert pv[EASY] != pv[GOOD]
    # Easy 间隔 > Good 间隔
    g = rate(c2, GOOD, dt.fromisoformat(c2["due"]))["scheduled_days"]
    e = rate(c2, EASY, dt.fromisoformat(c2["due"]))["scheduled_days"]
    assert e >= g >= 1
    r0 = retrievability(0, 10); r1 = retrievability(10, 10); r2 = retrievability(30, 10)
    assert 1.0 >= r0 > r1 > r2 and abs(r1 - 0.9) < 0.001
    print("FSRS 自检通过 ✓  (New→Learning→Review→Relearning→Review, R(10d,S=10)=%.3f)" % r1)
