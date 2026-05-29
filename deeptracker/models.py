"""Data models for DeepTracker — deep-tech funding & valuation tracking."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional


class Sector(Enum):
    SEMICONDUCTORS = "Semiconductors"
    SPACE_TECH = "Space Tech"
    AEROSPACE = "Aerospace & Defence"
    EVTOL = "eVTOL & Drones"
    BIOTECH = "Biotech & Life Sciences"
    AI_ML = "AI / ML Infrastructure"
    QUANTUM = "Quantum Computing"
    CLEANTECH = "Cleantech & Energy"
    ROBOTICS = "Robotics"
    OTHER = "Other Deep-Tech"


class Stage(Enum):
    PRE_SEED = "Pre-Seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    SERIES_D_PLUS = "Series D+"
    GROWTH = "Growth / PE"
    GRANT = "Govt Grant"


@dataclass
class FundingRound:
    """A single deep-tech funding round."""
    company: str
    sector: Sector
    stage: Stage
    amount_cr: float                       # round size in ₹ Crore
    date: date
    pre_money_cr: Optional[float] = None    # pre-money valuation in ₹ Crore
    lead_investor: str = ""
    investors: List[str] = field(default_factory=list)
    city: str = ""
    notes: str = ""

    @property
    def post_money_cr(self) -> Optional[float]:
        if self.pre_money_cr is not None:
            return self.pre_money_cr + self.amount_cr
        return None

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def quarter(self) -> str:
        q = (self.date.month - 1) // 3 + 1
        return f"Q{q} {self.date.year}"


@dataclass
class CompanyProfile:
    """Aggregated view of a single company's funding history."""
    name: str
    sector: Sector
    rounds: List[FundingRound] = field(default_factory=list)

    @property
    def total_raised_cr(self) -> float:
        return sum(r.amount_cr for r in self.rounds)

    @property
    def latest_round(self) -> Optional[FundingRound]:
        return max(self.rounds, key=lambda r: r.date) if self.rounds else None

    @property
    def latest_valuation_cr(self) -> Optional[float]:
        lr = self.latest_round
        return lr.post_money_cr if lr else None

    @property
    def num_rounds(self) -> int:
        return len(self.rounds)

    def valuation_step_up(self) -> Optional[float]:
        """Multiple between the two most recent post-money valuations."""
        valued = sorted([r for r in self.rounds if r.post_money_cr],
                        key=lambda r: r.date)
        if len(valued) < 2:
            return None
        prev, last = valued[-2].post_money_cr, valued[-1].post_money_cr
        return last / prev if prev else None
