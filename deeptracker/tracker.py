"""DealTracker — aggregate, filter, and analyze deep-tech funding rounds."""
from __future__ import annotations
import json
from datetime import date, datetime
from collections import defaultdict
from typing import List, Optional, Dict
from .models import FundingRound, CompanyProfile, Sector, Stage


class DealTracker:
    """
    Tracks deep-tech funding rounds and produces market analytics.

    Load rounds from a JSON file, or add them programmatically, then query:
      - total funding by sector / stage / quarter
      - most active investors
      - company funding histories
      - valuation step-ups
    """

    def __init__(self):
        self.rounds: List[FundingRound] = []

    # ── Ingestion ──────────────────────────────────────────────────────────

    def add(self, rnd: FundingRound) -> None:
        self.rounds.append(rnd)

    def load_json(self, path: str) -> int:
        """Load rounds from JSON. Returns number loaded."""
        with open(path) as f:
            data = json.load(f)
        count = 0
        for r in data.get("rounds", data if isinstance(data, list) else []):
            self.add(FundingRound(
                company=r["company"],
                sector=Sector(r["sector"]) if r["sector"] in [s.value for s in Sector]
                       else _sector_from_key(r["sector"]),
                stage=Stage(r["stage"]) if r["stage"] in [s.value for s in Stage]
                      else _stage_from_key(r["stage"]),
                amount_cr=float(r["amount_cr"]),
                date=_parse_date(r["date"]),
                pre_money_cr=r.get("pre_money_cr"),
                lead_investor=r.get("lead_investor", ""),
                investors=r.get("investors", []),
                city=r.get("city", ""),
                notes=r.get("notes", ""),
            ))
            count += 1
        return count

    # ── Filters ────────────────────────────────────────────────────────────

    def filter(self, sector: Optional[Sector] = None, stage: Optional[Stage] = None,
               year: Optional[int] = None, city: Optional[str] = None,
               min_amount_cr: Optional[float] = None) -> List[FundingRound]:
        out = self.rounds
        if sector is not None:
            out = [r for r in out if r.sector == sector]
        if stage is not None:
            out = [r for r in out if r.stage == stage]
        if year is not None:
            out = [r for r in out if r.year == year]
        if city is not None:
            out = [r for r in out if r.city.lower() == city.lower()]
        if min_amount_cr is not None:
            out = [r for r in out if r.amount_cr >= min_amount_cr]
        return out

    # ── Analytics ──────────────────────────────────────────────────────────

    @property
    def total_funding_cr(self) -> float:
        return sum(r.amount_cr for r in self.rounds)

    @property
    def deal_count(self) -> int:
        return len(self.rounds)

    def funding_by_sector(self) -> Dict[str, float]:
        out: Dict[str, float] = defaultdict(float)
        for r in self.rounds:
            out[r.sector.value] += r.amount_cr
        return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))

    def funding_by_stage(self) -> Dict[str, float]:
        out: Dict[str, float] = defaultdict(float)
        for r in self.rounds:
            out[r.stage.value] += r.amount_cr
        return dict(out)

    def funding_by_quarter(self) -> Dict[str, float]:
        out: Dict[str, float] = defaultdict(float)
        for r in self.rounds:
            out[r.quarter] += r.amount_cr
        # sort chronologically
        def key(q):
            qn, yr = q.split(" ")
            return (int(yr), int(qn[1:]))
        return dict(sorted(out.items(), key=lambda kv: key(kv[0])))

    def top_investors(self, n: int = 10) -> List[tuple]:
        """Most active investors by deal count (lead or participating)."""
        counts: Dict[str, int] = defaultdict(int)
        for r in self.rounds:
            seen = set()
            if r.lead_investor:
                seen.add(r.lead_investor)
            for inv in r.investors:
                seen.add(inv)
            for inv in seen:
                counts[inv] += 1
        return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def company_profile(self, name: str) -> Optional[CompanyProfile]:
        rounds = [r for r in self.rounds if r.company.lower() == name.lower()]
        if not rounds:
            return None
        return CompanyProfile(name=rounds[0].company, sector=rounds[0].sector, rounds=rounds)

    def companies(self) -> List[CompanyProfile]:
        by_company: Dict[str, List[FundingRound]] = defaultdict(list)
        for r in self.rounds:
            by_company[r.company].append(r)
        return [CompanyProfile(name=name, sector=rs[0].sector, rounds=rs)
                for name, rs in by_company.items()]

    def biggest_rounds(self, n: int = 10) -> List[FundingRound]:
        return sorted(self.rounds, key=lambda r: r.amount_cr, reverse=True)[:n]

    def average_round_size(self, stage: Optional[Stage] = None) -> Optional[float]:
        rs = self.filter(stage=stage) if stage else self.rounds
        return sum(r.amount_cr for r in rs) / len(rs) if rs else None


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_date(s) -> date:
    if isinstance(s, date):
        return s
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date: {s}")


def _sector_from_key(k: str) -> Sector:
    k = k.lower().replace(" ", "").replace("_", "")
    for s in Sector:
        if s.value.lower().replace(" ", "").replace("&", "").replace("/", "") in k or \
           k in s.value.lower().replace(" ", ""):
            return s
    return Sector.OTHER


def _stage_from_key(k: str) -> Stage:
    k = k.lower().replace(" ", "")
    for s in Stage:
        if s.value.lower().replace(" ", "").replace("+", "") in k:
            return s
    return Stage.SEED
