"""调度服务（docker compose 中的 scheduler 容器）：按 cron 定时跑管线与周报。"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app import pipeline, weekly

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("scheduler")


def safe_pipeline():
    try:
        pipeline.run()
    except Exception:  # noqa: BLE001
        log.exception("管线执行失败，等待下次调度")


def safe_weekly():
    try:
        weekly.run()
    except Exception:  # noqa: BLE001
        log.exception("周报生成失败")


def main():
    s = get_settings()
    sched = BlockingScheduler(timezone=s.timezone)
    sched.add_job(safe_pipeline, CronTrigger.from_crontab(s.pipeline_cron, timezone=s.timezone))
    sched.add_job(safe_weekly, CronTrigger.from_crontab(s.weekly_cron, timezone=s.timezone))
    log.info("调度已启动: 管线[%s] 周报[%s] 时区[%s]", s.pipeline_cron, s.weekly_cron, s.timezone)
    sched.start()


if __name__ == "__main__":
    main()
