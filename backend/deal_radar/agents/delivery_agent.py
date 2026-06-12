"""
Delivery Agent — runs daily at 08:00 UTC.
Sends a rich HTML email digest covering ALL watchlist companies.

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
from typing import List, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from deal_radar.db.models import Company, Signal, Inference
from deal_radar.scoring.rules import classify_score, SIGNAL_WEIGHTS

MIN_DIGEST_SCORE = 60
SIGNAL_LOOKBACK_HOURS = 24
FULL_STATUS_LOOKBACK_DAYS = 7

_SIGNAL_LABELS = {
    "hire_finance_ir":     "财务/IR 招聘",
    "hire_infra_burst":    "基础设施招聘",
    "github_commit_spike": "GitHub 提交激增",
    "pr_activity_surge":   "PR 活跃度激增",
    "founder_vc_interact": "创始人 × VC 互动",
    "team_expansion":      "团队扩张",
    "website_update":      "官网更新",
    "news":                "新闻报道",
}

_BAND_COLORS = {
    "HIGH":   ("#dc2626", "#fef2f2", "🔴"),
    "MEDIUM": ("#d97706", "#fffbeb", "🟡"),
    "LOW":    ("#16a34a", "#f0fdf4", "🟢"),
    "NOISE":  ("#6b7280", "#f9fafb", "⚪"),
}


# ── Data helpers ──────────────────────────────────────────────────────────────

def _get_company_data(db: Session, cutoff_signals: datetime, cutoff_inf: datetime):
    """Return list of dicts with company + recent signals + latest inference."""
    companies = db.query(Company).order_by(Company.name).all()
    result = []
    for company in companies:
        recent_signals: List[Signal] = (
            db.query(Signal)
            .filter(Signal.company_id == company.id, Signal.captured_at >= cutoff_signals)
            .order_by(Signal.captured_at.desc())
            .all()
        )
        latest_inf: Optional[Inference] = (
            db.query(Inference)
            .filter(Inference.company_id == company.id, Inference.created_at >= cutoff_inf)
            .order_by(Inference.confidence_score.desc())
            .first()
        )
        signal_types = list({s.signal_type for s in recent_signals})
        result.append({
            "company": company,
            "signals": recent_signals,
            "signal_types": signal_types,
            "inference": latest_inf,
        })
    return result


# ── Plain-text digest ─────────────────────────────────────────────────────────

def _format_block_text(inf: Inference, company: Company) -> str:
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


def generate_daily_digest_text(db: Session, as_of: datetime | None = None) -> str:
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
            blocks.append(_format_block_text(inf, company))

    return header + "\n\n".join(blocks)


# ── HTML email ────────────────────────────────────────────────────────────────

def _chip_html(label: str, color: str = "#e5e7eb", text_color: str = "#374151") -> str:
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'background:{color};color:{text_color};font-size:11px;font-weight:600;'
        f'margin:2px 2px 2px 0;">{label}</span>'
    )


def _signal_chips(signal_types: List[str]) -> str:
    chip_colors = {
        "hire_finance_ir":     ("#fef3c7", "#92400e"),
        "hire_infra_burst":    ("#dbeafe", "#1e40af"),
        "github_commit_spike": ("#d1fae5", "#065f46"),
        "pr_activity_surge":   ("#d1fae5", "#065f46"),
        "founder_vc_interact": ("#ede9fe", "#4c1d95"),
        "team_expansion":      ("#fce7f3", "#9d174d"),
        "website_update":      ("#e0f2fe", "#0c4a6e"),
        "news":                ("#f0fdf4", "#166534"),
    }
    chips = []
    for st in signal_types:
        label = _SIGNAL_LABELS.get(st, st)
        bg, fg = chip_colors.get(st, ("#e5e7eb", "#374151"))
        chips.append(_chip_html(label, bg, fg))
    return "".join(chips) if chips else _chip_html("无新信号", "#f3f4f6", "#9ca3af")


def _inference_card_html(inf: Inference, company: Company) -> str:
    band = classify_score(int(inf.confidence_score))
    border_color, bg_color, emoji = _BAND_COLORS.get(band["level"], ("#6b7280", "#f9fafb", "⚪"))
    return f"""
    <div style="border-left:4px solid {border_color};background:{bg_color};
                border-radius:0 8px 8px 0;padding:16px 20px;margin-bottom:16px;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <span style="font-size:20px;">{emoji}</span>
        <span style="font-size:18px;font-weight:700;color:#111827;">{company.name}</span>
        <span style="margin-left:auto;background:{border_color};color:#fff;
                     padding:2px 10px;border-radius:9999px;font-size:13px;font-weight:700;">
          {inf.confidence_score:.0f}/100
        </span>
      </div>
      <div style="color:#6b7280;font-size:13px;margin-bottom:8px;">
        预测事件：<strong style="color:#374151;">{inf.event_type}</strong>
        &nbsp;·&nbsp;{band['label']}
      </div>
      <div style="color:#374151;font-size:14px;line-height:1.6;margin-bottom:10px;">
        {inf.reasoning}
      </div>
      <div style="background:rgba(0,0,0,0.05);border-radius:6px;padding:8px 12px;
                  font-size:13px;color:#374151;">
        <strong>建议：</strong>{band['action']}
      </div>
    </div>"""


def _company_status_row_html(data: Dict) -> str:
    company: Company = data["company"]
    signals: List[Signal] = data["signals"]
    inf: Optional[Inference] = data["inference"]
    signal_types = data["signal_types"]

    score_html = ""
    if inf:
        band = classify_score(int(inf.confidence_score))
        border_color, _, emoji = _BAND_COLORS.get(band["level"], ("#6b7280", "#f9fafb", "⚪"))
        score_html = (
            f'<span style="background:{border_color};color:#fff;padding:2px 8px;'
            f'border-radius:9999px;font-size:12px;font-weight:700;">'
            f'{emoji} {inf.confidence_score:.0f}</span>'
        )
    else:
        score_html = '<span style="color:#9ca3af;font-size:12px;">—</span>'

    chips = _signal_chips(signal_types)
    sector = f'<span style="color:#6b7280;font-size:12px;">{company.sector}</span>' if company.sector else ""

    return f"""
    <tr style="border-bottom:1px solid #f3f4f6;">
      <td style="padding:12px 8px;font-weight:600;color:#111827;white-space:nowrap;">
        {company.name}<br>{sector}
      </td>
      <td style="padding:12px 8px;text-align:center;">{score_html}</td>
      <td style="padding:12px 8px;">{chips}</td>
      <td style="padding:12px 8px;text-align:center;color:#6b7280;font-size:13px;">
        {len(signals)}
      </td>
    </tr>"""


def generate_html_email(db: Session, as_of: datetime | None = None) -> str:
    as_of = as_of or datetime.utcnow()
    date_str = as_of.strftime("%Y年%m月%d日")
    cutoff_24h = as_of - timedelta(hours=SIGNAL_LOOKBACK_HOURS)
    cutoff_7d = as_of - timedelta(days=FULL_STATUS_LOOKBACK_DAYS)

    all_data = _get_company_data(db, cutoff_7d, cutoff_7d)

    # Split into priority buckets
    high = [d for d in all_data if d["inference"] and d["inference"].confidence_score >= 80]
    medium = [d for d in all_data if d["inference"] and 60 <= d["inference"].confidence_score < 80]
    active = [d for d in all_data if d["signals"] and not (d["inference"] and d["inference"].confidence_score >= 60)]
    quiet = [d for d in all_data if not d["signals"] and not (d["inference"] and d["inference"].confidence_score >= 60)]

    # Stats
    total_companies = len(all_data)
    total_signals_24h = sum(
        len([s for s in d["signals"] if s.captured_at >= cutoff_24h])
        for d in all_data
    )

    # Build priority sections
    high_section = ""
    if high:
        cards = "".join(_inference_card_html(d["inference"], d["company"]) for d in high)
        high_section = f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:18px;font-weight:700;color:#dc2626;margin:0 0 4px 0;
                     border-bottom:2px solid #dc2626;padding-bottom:8px;">
            🔴 高优先级 — 建议 48h 内接触 ({len(high)} 家)
          </h2>
          <p style="color:#6b7280;font-size:13px;margin:8px 0 16px 0;">
            综合信号评分 ≥ 80，建议立即启动接触流程
          </p>
          {cards}
        </div>"""

    medium_section = ""
    if medium:
        cards = "".join(_inference_card_html(d["inference"], d["company"]) for d in medium)
        medium_section = f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:18px;font-weight:700;color:#d97706;margin:0 0 4px 0;
                     border-bottom:2px solid #d97706;padding-bottom:8px;">
            🟡 观察跟踪 — 持续监控 ({len(medium)} 家)
          </h2>
          <p style="color:#6b7280;font-size:13px;margin:8px 0 16px 0;">
            评分 60-79，信号趋势值得持续关注
          </p>
          {cards}
        </div>"""

    # All companies status table
    all_rows = "".join(_company_status_row_html(d) for d in all_data)
    status_table = f"""
    <div style="margin-bottom:32px;">
      <h2 style="font-size:18px;font-weight:700;color:#374151;margin:0 0 16px 0;
                 border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
        📋 监控列表全览（过去 7 天）
      </h2>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f9fafb;">
            <th style="padding:10px 8px;text-align:left;color:#6b7280;font-weight:600;font-size:12px;">公司</th>
            <th style="padding:10px 8px;text-align:center;color:#6b7280;font-weight:600;font-size:12px;">评分</th>
            <th style="padding:10px 8px;text-align:left;color:#6b7280;font-weight:600;font-size:12px;">信号类型</th>
            <th style="padding:10px 8px;text-align:center;color:#6b7280;font-weight:600;font-size:12px;">信号数</th>
          </tr>
        </thead>
        <tbody>{all_rows}</tbody>
      </table>
      {'<p style="color:#9ca3af;font-size:13px;text-align:center;padding:16px;">暂无被追踪公司，请添加监控列表。</p>' if not all_data else ""}
    </div>"""

    no_alerts = not high and not medium
    summary_bg = "#f0fdf4" if no_alerts else "#fffbeb"
    summary_border = "#16a34a" if no_alerts else "#d97706"
    summary_text = "今日无高置信度信号，市场相对平静。" if no_alerts else f"发现 <strong>{len(high) + len(medium)}</strong> 家公司有重要信号。"

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Deal Radar 日报</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:24px 16px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
                border-radius:12px;padding:28px 32px;margin-bottom:24px;color:#fff;">
      <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;
                  opacity:0.75;margin-bottom:8px;">UKMC GP Intelligence</div>
      <h1 style="margin:0;font-size:26px;font-weight:800;">📡 Deal Radar 日报</h1>
      <div style="margin-top:8px;font-size:14px;opacity:0.85;">{date_str}</div>
      <!-- Stats row -->
      <div style="display:flex;gap:24px;margin-top:20px;flex-wrap:wrap;">
        <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:10px 16px;min-width:100px;">
          <div style="font-size:22px;font-weight:800;">{total_companies}</div>
          <div style="font-size:11px;opacity:0.8;">监控公司</div>
        </div>
        <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:10px 16px;min-width:100px;">
          <div style="font-size:22px;font-weight:800;">{total_signals_24h}</div>
          <div style="font-size:11px;opacity:0.8;">过去24h信号</div>
        </div>
        <div style="background:rgba(220,38,38,0.4);border-radius:8px;padding:10px 16px;min-width:100px;">
          <div style="font-size:22px;font-weight:800;">{len(high)}</div>
          <div style="font-size:11px;opacity:0.8;">🔴 高优先级</div>
        </div>
        <div style="background:rgba(217,119,6,0.4);border-radius:8px;padding:10px 16px;min-width:100px;">
          <div style="font-size:22px;font-weight:800;">{len(medium)}</div>
          <div style="font-size:11px;opacity:0.8;">🟡 观察跟踪</div>
        </div>
      </div>
    </div>

    <!-- Summary banner -->
    <div style="background:{summary_bg};border:1px solid {summary_border};border-radius:8px;
                padding:14px 18px;margin-bottom:24px;color:#374151;font-size:14px;">
      <strong>今日摘要：</strong>{summary_text}
      过去 7 天共追踪到 <strong>{sum(len(d['signals']) for d in all_data)}</strong> 条信号。
    </div>

    <!-- Main content -->
    <div style="background:#fff;border-radius:12px;padding:28px 28px;margin-bottom:24px;
                box-shadow:0 1px 3px rgba(0,0,0,0.1);">
      {high_section}
      {medium_section}
      {status_table}
    </div>

    <!-- Footer -->
    <div style="text-align:center;color:#9ca3af;font-size:12px;padding:16px;">
      <p style="margin:0;">Deal Radar · UKMC GP Dashboard</p>
      <p style="margin:4px 0 0 0;">每日 08:00 UTC 自动发送 · 信号采集每 6 小时一次</p>
      <p style="margin:8px 0 0 0;font-size:11px;">
        评分说明：🔴 80-100 高优先级 &nbsp;·&nbsp; 🟡 60-79 观察跟踪 &nbsp;·&nbsp; 🟢 40-59 早期信号
      </p>
    </div>
  </div>
</body>
</html>"""
    return html


# ── Email ─────────────────────────────────────────────────────────────────────

def _send_email(html_body: str, plain_body: str, to_addr: str, date_str: str) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    pwd = os.getenv("SMTP_PASS", "")

    if not user or not pwd:
        raise RuntimeError("SMTP credentials not configured (SMTP_USER / SMTP_PASS).")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📡 Deal Radar 日报 — {date_str}"
    msg["From"] = f"Deal Radar <{user}>"
    msg["To"] = to_addr

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(host, port) as srv:
        srv.ehlo()
        srv.starttls()
        srv.login(user, pwd)
        srv.sendmail(user, to_addr, msg.as_string())


# ── Feishu ────────────────────────────────────────────────────────────────────

def _feishu_card(inf: Inference, company: Company) -> dict:
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
        "text": digest[:3000],
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
    date_str = as_of.strftime("%Y-%m-%d")

    html_body = generate_html_email(db, as_of)
    plain_body = generate_daily_digest_text(db, as_of)

    # Email dispatch
    recipients = [r.strip() for r in os.getenv("DIGEST_RECIPIENTS", "").split(",") if r.strip()]
    dispatched = 0
    for addr in recipients:
        try:
            _send_email(html_body, plain_body, addr, date_str)
            print(f"[DeliveryAgent] ✓ Email → {addr}")
            dispatched += 1
        except Exception as exc:
            print(f"[DeliveryAgent] ✗ Email failed ({addr}): {exc}")

    # Feishu + Slack (structured channels use plain inferences list)
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

    import asyncio

    async def _async_channels():
        tasks = [_send_feishu(db, inferences, date_str), _send_slack(plain_body)]
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
        print(plain_body)

    return plain_body


# kept for backwards-compat (CLI / tests call this)
def generate_daily_digest(db: Session, as_of: datetime | None = None) -> str:
    return generate_daily_digest_text(db, as_of)
