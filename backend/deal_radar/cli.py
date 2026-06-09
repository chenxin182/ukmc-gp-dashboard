"""
Deal Radar CLI — management tool for the watchlist and agents.

Usage:
  python -m deal_radar.cli <command> [options]

Commands:
  companies list                   List watched companies
  companies add <name>             Add company to watchlist
  companies remove <id>            Remove company from watchlist

  signals run                      Run Signal Agent now
  signals show <company_id>        Show recent signals for a company

  inference run                    Run Inference Agent now
  inference list [--days N]        List recent inferences

  digest preview                   Print today's digest to stdout
  digest send                      Run Delivery Agent (sends to configured channels)

  backtest [--mode simulation]     Run backtest report

  seed                             Import funding_events.csv + demo companies
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta

from deal_radar.db.database import SessionLocal, init_db
from deal_radar.db.models import Company, Inference, Signal
from deal_radar.scoring.rules import classify_score


def _db():
    return SessionLocal()


# ── companies ────────────────────────────────────────────────────────────────

def cmd_companies_list(_args):
    db = _db()
    companies = db.query(Company).order_by(Company.name).all()
    if not companies:
        print("Watchlist is empty. Add a company with: companies add <name>")
        return

    print(f"\n{'ID':>4}  {'Name':<25} {'GitHub':<22} {'Sector':<20} {'Stage'}")
    print(f"{'─'*4}  {'─'*25} {'─'*22} {'─'*20} {'─'*12}")
    for c in companies:
        print(f"{c.id:>4}  {c.name:<25} {(c.github_org or '—'):<22} "
              f"{(c.sector or '—'):<20} {c.stage or '—'}")
    print()
    db.close()


def cmd_companies_add(args):
    db = _db()
    existing = db.query(Company).filter_by(name=args.name).first()
    if existing:
        print(f"Company '{args.name}' already exists (id={existing.id}).")
        db.close()
        return

    company = Company(
        name=args.name,
        domain=getattr(args, "domain", None),
        github_org=getattr(args, "github", None),
        twitter_handle=getattr(args, "twitter", None),
        founder_twitter=getattr(args, "founder_twitter", None),
        sector=getattr(args, "sector", None),
        stage=getattr(args, "stage", None),
        greenhouse_token=getattr(args, "greenhouse", None),
        lever_slug=getattr(args, "lever", None),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"✓ Added '{company.name}' (id={company.id})")
    db.close()


def cmd_companies_remove(args):
    db = _db()
    company = db.get(Company, args.id)
    if not company:
        print(f"No company with id={args.id}")
        db.close()
        return
    name = company.name
    db.delete(company)
    db.commit()
    print(f"✓ Removed '{name}' (id={args.id}) and all associated signals/inferences.")
    db.close()


# ── signals ──────────────────────────────────────────────────────────────────

def cmd_signals_run(_args):
    from deal_radar.agents.signal_agent import run_signal_agent
    db = _db()
    print("[CLI] Running Signal Agent...")
    new = asyncio.run(run_signal_agent(db))
    print(f"[CLI] Done. {len(new)} new signals captured.")
    db.close()


def cmd_signals_show(args):
    db = _db()
    company = db.get(Company, args.company_id)
    if not company:
        print(f"Company id={args.company_id} not found.")
        db.close()
        return

    days = getattr(args, "days", 30)
    cutoff = datetime.utcnow() - timedelta(days=days)
    signals = (
        db.query(Signal)
        .filter(Signal.company_id == args.company_id, Signal.captured_at >= cutoff)
        .order_by(Signal.captured_at.desc())
        .all()
    )

    print(f"\nSignals for '{company.name}' (last {days}d): {len(signals)}\n")
    print(f"{'Date':<22} {'Type':<24} {'Source'}")
    print(f"{'─'*22} {'─'*24} {'─'*40}")
    for s in signals:
        print(f"{s.captured_at.strftime('%Y-%m-%d %H:%M'):<22} {s.signal_type:<24} "
              f"{(s.source_url or '—')[:60]}")
    print()
    db.close()


# ── inference ────────────────────────────────────────────────────────────────

def cmd_inference_run(_args):
    from deal_radar.agents.inference_agent import run_inference_agent
    db = _db()
    print("[CLI] Running Inference Agent...")
    infs = run_inference_agent(db)
    print(f"[CLI] Done. {len(infs)} inferences created.")
    db.close()


def cmd_inference_list(args):
    db = _db()
    days = getattr(args, "days", 7)
    min_score = getattr(args, "min_score", 0)
    cutoff = datetime.utcnow() - timedelta(days=days)

    infs = (
        db.query(Inference)
        .filter(Inference.created_at >= cutoff, Inference.confidence_score >= min_score)
        .order_by(Inference.confidence_score.desc())
        .all()
    )

    print(f"\nInferences — last {days}d (score ≥ {min_score}): {len(infs)}\n")
    print(f"{'ID':>5}  {'Score':>5}  {'Band':<6}  {'Event':<14}  {'Company'}")
    print(f"{'─'*5}  {'─'*5}  {'─'*6}  {'─'*14}  {'─'*25}")
    for inf in infs:
        company = db.get(Company, inf.company_id)
        name = company.name if company else "?"
        band = classify_score(int(inf.confidence_score))
        print(f"{inf.id:>5}  {inf.confidence_score:>5.0f}  "
              f"{band['emoji']} {band['level'][:4]:<4}  {inf.event_type:<14}  {name}")
    print()
    db.close()


# ── digest ────────────────────────────────────────────────────────────────────

def cmd_digest_preview(_args):
    from deal_radar.agents.delivery_agent import generate_daily_digest
    db = _db()
    print(generate_daily_digest(db))
    db.close()


def cmd_digest_send(_args):
    from deal_radar.agents.delivery_agent import run_delivery_agent
    db = _db()
    print("[CLI] Running Delivery Agent...")
    run_delivery_agent(db)
    db.close()


# ── backtest ──────────────────────────────────────────────────────────────────

def cmd_backtest(args):
    from deal_radar.backtest import run_backtest
    db = _db()
    mode = getattr(args, "mode", "simulation")
    run_backtest(db, mode=mode)
    db.close()


# ── seed ──────────────────────────────────────────────────────────────────────

def cmd_seed(_args):
    from deal_radar.db.seed import import_funding_events, seed_demo_watchlist, CSV_PATH
    init_db()
    db = _db()
    n_events = import_funding_events(db, CSV_PATH)
    n_companies = seed_demo_watchlist(db)
    print(f"✓ Imported {n_events} funding events, added {n_companies} demo companies.")
    db.close()


# ── Arg parser ────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deal_radar.cli",
        description="Deal Radar CLI",
    )
    sub = parser.add_subparsers(dest="group", required=True)

    # companies
    co = sub.add_parser("companies")
    co_sub = co.add_subparsers(dest="action", required=True)

    co_sub.add_parser("list")

    co_add = co_sub.add_parser("add")
    co_add.add_argument("name")
    co_add.add_argument("--domain")
    co_add.add_argument("--github")
    co_add.add_argument("--twitter")
    co_add.add_argument("--founder-twitter", dest="founder_twitter")
    co_add.add_argument("--sector")
    co_add.add_argument("--stage")
    co_add.add_argument("--greenhouse")
    co_add.add_argument("--lever")

    co_rm = co_sub.add_parser("remove")
    co_rm.add_argument("id", type=int)

    # signals
    sg = sub.add_parser("signals")
    sg_sub = sg.add_subparsers(dest="action", required=True)
    sg_sub.add_parser("run")
    sg_show = sg_sub.add_parser("show")
    sg_show.add_argument("company_id", type=int)
    sg_show.add_argument("--days", type=int, default=30)

    # inference
    inf = sub.add_parser("inference")
    inf_sub = inf.add_subparsers(dest="action", required=True)
    inf_sub.add_parser("run")
    inf_list = inf_sub.add_parser("list")
    inf_list.add_argument("--days", type=int, default=7)
    inf_list.add_argument("--min-score", dest="min_score", type=int, default=0)

    # digest
    dg = sub.add_parser("digest")
    dg_sub = dg.add_subparsers(dest="action", required=True)
    dg_sub.add_parser("preview")
    dg_sub.add_parser("send")

    # backtest
    bt = sub.add_parser("backtest")
    bt.add_argument("--mode", choices=["simulation", "feedback", "both"], default="simulation")

    # seed
    sub.add_parser("seed")

    return parser


DISPATCH = {
    ("companies", "list"):     cmd_companies_list,
    ("companies", "add"):      cmd_companies_add,
    ("companies", "remove"):   cmd_companies_remove,
    ("signals",   "run"):      cmd_signals_run,
    ("signals",   "show"):     cmd_signals_show,
    ("inference", "run"):      cmd_inference_run,
    ("inference", "list"):     cmd_inference_list,
    ("digest",    "preview"):  cmd_digest_preview,
    ("digest",    "send"):     cmd_digest_send,
    ("backtest",  None):       cmd_backtest,
    ("seed",      None):       cmd_seed,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    action = getattr(args, "action", None)
    key = (args.group, action)
    fn = DISPATCH.get(key)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
