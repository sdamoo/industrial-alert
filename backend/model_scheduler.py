"""APScheduler configuration for model scheduled execution."""

import sqlite3
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import DB_PATH

# Global scheduler instance
scheduler = BackgroundScheduler()

# Cycle -> CronTrigger mapping
CYCLE_TRIGGER_MAP = {
    "每小时": CronTrigger(minute=0),
    "每日": CronTrigger(hour=6, minute=0),
    "每周": CronTrigger(day_of_week="mon", hour=6, minute=0),
    "每月": CronTrigger(day=1, hour=6, minute=0),
}


def run_model_job(model_id: int, file_path: str):
    """Scheduled job callback: simulate model execution and update last_run_at."""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute(
            "UPDATE ai_models SET last_run_at = ?, updated_at = ? WHERE id = ?",
            (now_str, now_str, model_id),
        )
        conn.commit()
        conn.close()
        print(f"[Scheduler] 模型 {model_id} 已执行，文件: {file_path}")
    except Exception as e:
        print(f"[Scheduler] 模型 {model_id} 执行失败: {e}")


def add_model_job(model_id: int, cycle: str, file_path: str):
    """Add a scheduled job for a model."""
    trigger = CYCLE_TRIGGER_MAP.get(cycle)
    if trigger is None:
        print(f"[Scheduler] 未知的运行周期: {cycle}，跳过调度")
        return

    remove_model_job(model_id)

    job_id = f"model_{model_id}"
    scheduler.add_job(
        run_model_job,
        trigger=trigger,
        args=[model_id, file_path],
        id=job_id,
        replace_existing=True,
    )
    print(f"[Scheduler] 已添加定时任务: {job_id}，周期: {cycle}")


def remove_model_job(model_id: int):
    """Remove a scheduled job for a model."""
    job_id = f"model_{model_id}"
    try:
        scheduler.remove_job(job_id)
        print(f"[Scheduler] 已移除定时任务: {job_id}")
    except Exception:
        pass


def restore_running_jobs():
    """Restore scheduled jobs for all models with status='运行中' on startup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, cycle, file_path FROM ai_models WHERE status = '运行中'"
    ).fetchall()
    conn.close()

    for row in rows:
        add_model_job(row["id"], row["cycle"], row["file_path"])
    print(f"[Scheduler] 已恢复 {len(rows)} 个运行中的模型任务")


def start_scheduler():
    """Start the scheduler."""
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] 调度器已启动")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] 调度器已关闭")
