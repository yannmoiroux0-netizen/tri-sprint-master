#!/usr/bin/env python3
import argparse, json, sys
from datetime import datetime
from core.plan_engine import build_week
from core.scheduler import apply_guardrails, apply_imprevu
from core.exports import to_csv, to_markdown, to_ics

def main():
    p = argparse.ArgumentParser(description="Tri Sprint Master — CLI")
    p.add_argument("--date", required=True, help="YYYY-MM-DD (lundi de la semaine cible ou n'importe quel jour)")
    p.add_argument("--fatigue", type=int, default=5, help="1-10")
    p.add_argument("--imprevu-day", help="LUN/MAR/MER/JEU/VEN/SAM/DIM")
    p.add_argument("--imprevu-sports", help="Liste separee par virgules: Nat,Velo,CàP,Renfo,Mobilite")
    p.add_argument("--export", choices=["csv","md","ics"], default="md")
    args = p.parse_args()

    d = datetime.strptime(args.date, "%Y-%m-%d").date()
    wk = build_week(d)
    wk = apply_guardrails(wk, fatigue_score=args.fatigue)

    if args.imprevu_day and args.imprevu_sports:
        banned = [s.strip() for s in args.imprevu_sports.split(",")]
        wk = apply_imprevu(wk, args.imprevu_day, banned)

    if args.export=="csv":
        sys.stdout.write(to_csv(wk))
    elif args.export=="ics":
        sys.stdout.write(to_ics(wk))
    else:
        sys.stdout.write(to_markdown(wk))

if __name__=="__main__":
    main()
