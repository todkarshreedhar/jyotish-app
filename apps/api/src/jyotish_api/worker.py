"""Background jobs (Celery + Redis): PDF reports, clean-up, alerts.

Run locally:  uv run celery -A jyotish_api.worker worker --beat -l info
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import delete, select

from jyotish_api.db import SessionLocal
from jyotish_api.models import Report
from jyotish_api.settings import settings

log = logging.getLogger(__name__)

celery = Celery("jyotish", broker=settings.redis_url, backend=None)
celery.conf.update(
    task_always_eager=settings.tasks_eager or settings.environment == "test",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="Asia/Kolkata",
    beat_schedule={
        "purge-expired-reports": {"task": "jyotish_api.worker.purge_expired_reports", "schedule": crontab(minute=15, hour=3)},
        "daily-alerts": {"task": "jyotish_api.worker.send_daily_alerts", "schedule": crontab(minute=0, hour=6)},
    },
)


@celery.task(name="jyotish_api.worker.build_report")
def build_report(report_id: str) -> str:
    from jyotish_api.models import Profile, User
    from jyotish_api.routers.profiles import _inputs, profile_out
    from jyotish_api.services import charts, pdf

    with SessionLocal() as db:
        r = db.get(Report, uuid.UUID(report_id))
        if r is None:
            return "missing"
        r.status = "running"
        db.commit()
        try:
            user = db.get(User, r.user_id)
            p = db.get(Profile, r.profile_id)
            if user is None or p is None:
                raise LookupError("the profile or its owner was deleted")
            style = (p.settings or {}).get("chart_style", "north")
            if r.kind == "match":
                from jyotish_api.routers.tools import match_data

                if r.partner_profile_id is None:
                    raise LookupError("a match report needs a second profile")
                data = match_data(db, user, str(r.profile_id), str(r.partner_profile_id), r.lang)
                r.pdf = pdf.match_pdf(data, r.lang, style, user)
            else:
                birth, cs = _inputs(p)
                c = charts.chart_dict(birth, cs, ("D1", "D9"))
                r.pdf = pdf.natal_pdf(profile_out(p), c, charts.readings(c, r.lang), r.lang, style, user)
            r.status = "ready"
            r.finished_at = datetime.now(UTC)
            r.expires_at = r.finished_at + timedelta(days=settings.report_retention_days)
        except Exception as exc:  # report the failure to the user, keep the worker alive
            log.exception("report %s failed", report_id)
            r.status = "failed"
            r.error = type(exc).__name__
        db.commit()
        return r.status


@celery.task(name="jyotish_api.worker.purge_expired_reports")
def purge_expired_reports() -> int:
    with SessionLocal() as db:
        res = db.execute(delete(Report).where(Report.expires_at < datetime.now(UTC)))
        db.commit()
        return int(res.rowcount or 0)  # type: ignore[attr-defined]


@celery.task(name="jyotish_api.worker.send_daily_alerts")
def send_daily_alerts() -> int:
    from jyotish_api.services.alerts import run_daily

    with SessionLocal() as db:
        return run_daily(db, datetime.now(UTC))


def stuck_reports() -> list[str]:
    with SessionLocal() as db:
        cutoff = datetime.now(UTC) - timedelta(minutes=10)
        return [str(r.id) for r in db.scalars(select(Report).where(Report.status == "queued", Report.created_at < cutoff))]
