"""
Delivery Agent — runs daily at 08:00 UTC.
Generates a Markdown digest of high-confidence inferences and optionally emails it.
"""
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Inference
from deal_radar.scoring.rules import classify_score

MIN_DIGEST_SCORE = 60


def _format_block(inf: Inference, company: Company) -> str:
    band = classify_score(int(inf.confidence_score))
    divider = "━" * 52
    lines = [
        divider,
        f"{band['emoji']} [{inf.confidence_score:.0f}分] {company.name}",
        divider,
        f"推断事件: {inf.event_type}",
        f"置信度:   {inf.confidence_score:.0f}/100",
        "",
        "推理:",
        f"  {inf.reasoning}",
        "",
        "建议动作:",
        f"  → {band['action']}",
        divider,
    ]
    return "\n".join(lines)


def generate_daily_digest(db: Session, as_of: datetime | None = None) -> str:
    as_of = as_of or datetime.utcnow()
    cutoff = as_of - timedelta(hours=24)

    inferences: List[Inference] = (
        db.query(Inference)
        .filter(
            Inference.created_at >= cutoff,
            Inference.confidence_score >= MIN_DIGEST_SCORE,
        )
        .order_by(Inference.confidence_score.desc())
        .all()
    )

    date_str = as_of.strftime("%Y-%m-%d")
    header = f"# Deal Radar 日报 — {date_str}\n"

    if not inferences:
        return header + "\n今日无高置信度信号（阈值 ≥ 60）。\n"

    header += f"共 **{len(inferences)}** 条情报（置信度 ≥ {MIN_DIGEST_SCORE}）\n\n"

    blocks = []
    for inf in inferences:
        company = db.get(Company, inf.company_id)
        if company:
            blocks.append(_format_block(inf, company))

    return header + "\n\n".join(blocks)


def _send_email(body: str, to_addr: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pwd = os.getenv("SMTP_PASS", "")

    if not user or not pwd:
        raise RuntimeError("SMTP credentials not configured (SMTP_USER / SMTP_PASS).")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Deal Radar 日报 — {datetime.utcnow().strftime('%Y-%m-%d')}"
    msg["From"] = user
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(host, port) as srv:
        srv.ehlo()
        srv.starttls()
        srv.login(user, pwd)
        srv.sendmail(user, to_addr, msg.as_string())


def run_delivery_agent(db: Session) -> str:
    digest = generate_daily_digest(db)
    recipients = [r.strip() for r in os.getenv("DIGEST_RECIPIENTS", "").split(",") if r.strip()]

    if recipients:
        for addr in recipients:
            try:
                _send_email(digest, addr)
                print(f"[DeliveryAgent] ✓ Sent to {addr}")
            except Exception as exc:
                print(f"[DeliveryAgent] ✗ Failed to send to {addr}: {exc}")
    else:
        print("[DeliveryAgent] No DIGEST_RECIPIENTS set. Digest preview:\n")
        print(digest)

    return digest
