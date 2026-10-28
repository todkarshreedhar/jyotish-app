"""PDF reports as background jobs (US-48, US-49, US-68)."""

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select

from jyotish_api.models import Report
from jyotish_api.routers.profiles import get_owned
from jyotish_api.security import DB, ConsentedUser

router = APIRouter(prefix="/v1/reports", tags=["reports"])


class ReportIn(BaseModel):
    profile_id: str
    kind: Literal["natal", "match"] = "natal"
    partner_profile_id: str | None = None
    lang: Literal["en", "hi", "mr"] = "en"


def report_out(r: Report) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "kind": r.kind,
        "lang": r.lang,
        "status": r.status,
        "profile_id": str(r.profile_id) if r.profile_id else None,
        "partner_profile_id": str(r.partner_profile_id) if r.partner_profile_id else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        "error": r.error,
    }


@router.post("", status_code=202)
def create_report(body: ReportIn, user: ConsentedUser, db: DB) -> dict[str, Any]:
    p = get_owned(db, user, body.profile_id)
    partner = None
    if body.kind == "match":
        if not body.partner_profile_id:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "partner_profile_id is required for a match report")
        partner = get_owned(db, user, body.partner_profile_id)
    r = Report(
        user_id=user.id, profile_id=p.id, partner_profile_id=partner.id if partner else None, kind=body.kind, lang=body.lang
    )
    db.add(r)
    db.commit()
    from jyotish_api.worker import build_report

    build_report.delay(str(r.id))
    db.refresh(r)
    return report_out(r)


@router.get("")
def list_reports(user: ConsentedUser, db: DB) -> dict[str, Any]:
    rows = db.scalars(select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc()).limit(50))
    return {"items": [report_out(r) for r in rows]}


def _owned(db: DB, user: Any, report_id: str) -> Report:
    try:
        r = db.get(Report, uuid.UUID(report_id))
    except ValueError:
        r = None
    if r is None or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return r


@router.get("/{report_id}")
def get_report(report_id: str, user: ConsentedUser, db: DB) -> dict[str, Any]:
    return report_out(_owned(db, user, report_id))


@router.get("/{report_id}/download")
def download(report_id: str, user: ConsentedUser, db: DB) -> Response:
    r = _owned(db, user, report_id)
    if r.status != "ready" or r.pdf is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "report is not ready")
    if r.expires_at and r.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_410_GONE, "report has expired")
    return Response(
        bytes(r.pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="jyotish-{r.kind}-{str(r.id)[:8]}.pdf"'},
    )


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, user: ConsentedUser, db: DB) -> Response:
    db.delete(_owned(db, user, report_id))
    db.commit()
    return Response(status_code=204)
