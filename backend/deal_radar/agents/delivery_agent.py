"""
Delivery Agent — runs daily at 08:00 UTC.
Supports: email, Feishu webhook, Slack webhook.

Channel selection via env vars:
  DIGEST_RECIPIENTS   — comma-separated email addresses
  FEISHU_WEBHOOK_URL  — Feishu bot webhook URL
  SLACK_WEBHOOK_URL   — Slack incoming webhook URL
"""
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import httpx
from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Inference
from deal_radar.scoring.rules import classify_score

MIN_DIGEST_SCORE = 60


# ── Formatters ────────────────────────────────────────────────────────────────

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


def _feishu_card(inf: Inference, company: Company) -> dict:
    """Format one inference as a Feishu interactive card element."""
    band = classify_score(int(inf.confidence_score))
    return {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": (
                f"**{band['emoji']} {company.name}** — {inf.confidence_score:.0f}/100\n"
                f"事件: `{inf.event_type}` | {band['label']}\n"
                f"> {inf.reasoning[:120]}…\n"
                f"→ {band['action']}"
            ),
        },
    }


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


# ── Email ─────────────────────────────────────────────────────────────────────

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


# ── Feishu ────────────────────────────────────────────────────────────────────

async def _send_feishu(db: Session, inferences: List[Inference], date_str: str) -> None:
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "")
    if not webhook_url:
        return

    elements = []
    for inf in inferences:
        company = db.get(Company, inf.company_id)
        if company:
            elements.append(_feishu_card(inf, company))
            elements.append({"tag": "hr"})

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📡 Deal Radar 日报 {date_str}"},
                "template": "blue",
            },
            "elements": elements or [
                {"tag": "div", "text": {"tag": "plain_text", "content": "今日无高置信度信号。"}}
            ],
        },
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(webhook_url, json=payload, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Feishu webhook returned {r.status_code}: {r.text[:200]}")


# ── Slack ─────────────────────────────────────────────────────────────────────

async def _send_slack(digest: str) -> None:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return

    payload = {
        "text": digest[:3000],   # Slack message limit
        "username": "Deal Radar",
        "icon_emoji": ":radar:",
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(webhook_url, json=payload, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"Slack webhook returned {r.status_code}: {r.text[:200]}")


# ── Main entry ────────────────────────────────────────────────────────────────

def run_delivery_agent(db: Session) -> str:
    as_of = datetime.utcnow()
    digest = generate_daily_digest(db, as_of)
    date_str = as_of.strftime("%Y-%m-%d")

    # Collect inferences for structured channels
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

    dispatched = 0

    # Email
    recipients = [r.strip() for r in os.getenv("DIGEST_RECIPIENTS", "").split(",") if r.strip()]
    for addr in recipients:
        try:
            _send_email(digest, addr)
            print(f"[DeliveryAgent] ✓ Email → {addr}")
            dispatched += 1
        except Exception as exc:
            print(f"[DeliveryAgent] ✗ Email failed ({addr}): {exc}")

    # Feishu + Slack use async; run via asyncio if called synchronously
    import asyncio

    async def _async_channels():
        tasks = [_send_feishu(db, inferences, date_str), _send_slack(digest)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(["Feishu", "Slack"], results):
            if isinstance(result, Exception):
                print(f"[DeliveryAgent] ✗ {name} failed: {result}")
            elif os.getenv(f"{name.upper()}_WEBHOOK_URL"):
                print(f"[DeliveryAgent] ✓ {name} sent.")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_async_channels())
        else:
            loop.run_until_complete(_async_channels())
    except Exception as exc:
        print(f"[DeliveryAgent] ✗ Async channels error: {exc}")

    if dispatched == 0 and not os.getenv("FEISHU_WEBHOOK_URL") and not os.getenv("SLACK_WEBHOOK_URL"):
        print("[DeliveryAgent] No channels configured. Digest preview:\n")
        print(digest)

    return digest
