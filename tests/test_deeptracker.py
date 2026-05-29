"""Tests for DeepTracker."""
from __future__ import annotations
import json
import pytest
from datetime import date
from deeptracker.models import FundingRound, CompanyProfile, Sector, Stage
from deeptracker.tracker import DealTracker, _parse_date, _sector_from_key, _stage_from_key


def mk(company="Acme", sector=Sector.SEMICONDUCTORS, stage=Stage.SERIES_A,
       amount=100.0, d=date(2025, 6, 1), pre=None, lead="Fund A", investors=None,
       city="Bengaluru"):
    return FundingRound(company=company, sector=sector, stage=stage, amount_cr=amount,
                        date=d, pre_money_cr=pre, lead_investor=lead,
                        investors=investors or [], city=city)


# ── FundingRound model ────────────────────────────────────────────────────────

def test_post_money():
    r = mk(amount=50, pre=200)
    assert r.post_money_cr == 250

def test_post_money_none_without_pre():
    r = mk(pre=None)
    assert r.post_money_cr is None

def test_quarter():
    assert mk(d=date(2025, 1, 15)).quarter == "Q1 2025"
    assert mk(d=date(2025, 4, 1)).quarter == "Q2 2025"
    assert mk(d=date(2025, 12, 31)).quarter == "Q4 2025"

def test_year():
    assert mk(d=date(2024, 7, 1)).year == 2024


# ── DealTracker basics ────────────────────────────────────────────────────────

def test_add_and_total():
    t = DealTracker()
    t.add(mk(amount=100))
    t.add(mk(amount=150))
    assert t.deal_count == 2
    assert t.total_funding_cr == 250

def test_funding_by_sector():
    t = DealTracker()
    t.add(mk(sector=Sector.SEMICONDUCTORS, amount=100))
    t.add(mk(sector=Sector.SPACE_TECH, amount=60))
    t.add(mk(sector=Sector.SEMICONDUCTORS, amount=40))
    by = t.funding_by_sector()
    assert by["Semiconductors"] == 140
    assert by["Space Tech"] == 60
    # sorted descending
    assert list(by.keys())[0] == "Semiconductors"

def test_funding_by_stage():
    t = DealTracker()
    t.add(mk(stage=Stage.SEED, amount=10))
    t.add(mk(stage=Stage.SERIES_A, amount=100))
    by = t.funding_by_stage()
    assert by["Seed"] == 10
    assert by["Series A"] == 100

def test_funding_by_quarter_sorted():
    t = DealTracker()
    t.add(mk(d=date(2025, 5, 1), amount=50))
    t.add(mk(d=date(2024, 2, 1), amount=30))
    t.add(mk(d=date(2025, 1, 1), amount=20))
    q = t.funding_by_quarter()
    keys = list(q.keys())
    assert keys[0] == "Q1 2024"  # earliest first
    assert keys[-1] == "Q2 2025"


# ── Filters ───────────────────────────────────────────────────────────────────

def test_filter_sector():
    t = DealTracker()
    t.add(mk(sector=Sector.SPACE_TECH))
    t.add(mk(sector=Sector.BIOTECH))
    assert len(t.filter(sector=Sector.SPACE_TECH)) == 1

def test_filter_year_and_min_amount():
    t = DealTracker()
    t.add(mk(d=date(2024, 1, 1), amount=10))
    t.add(mk(d=date(2025, 1, 1), amount=500))
    assert len(t.filter(year=2025)) == 1
    assert len(t.filter(min_amount_cr=100)) == 1

def test_filter_city():
    t = DealTracker()
    t.add(mk(city="Hyderabad"))
    t.add(mk(city="Bengaluru"))
    assert len(t.filter(city="hyderabad")) == 1  # case insensitive


# ── Investors ─────────────────────────────────────────────────────────────────

def test_top_investors():
    t = DealTracker()
    t.add(mk(lead="Peak XV", investors=["Blume"]))
    t.add(mk(lead="Peak XV", investors=["Accel"]))
    t.add(mk(lead="Accel", investors=[]))
    top = t.top_investors()
    names = dict(top)
    assert names["Peak XV"] == 2
    assert names["Accel"] == 2

def test_top_investors_no_double_count():
    # Same investor as lead AND in investors list counts once per deal
    t = DealTracker()
    t.add(mk(lead="Peak XV", investors=["Peak XV"]))
    top = dict(t.top_investors())
    assert top["Peak XV"] == 1


# ── Company profile ───────────────────────────────────────────────────────────

def test_company_profile_total():
    t = DealTracker()
    t.add(mk(company="Agnikul", amount=100, d=date(2023, 1, 1)))
    t.add(mk(company="Agnikul", amount=200, d=date(2024, 1, 1)))
    p = t.company_profile("Agnikul")
    assert p.total_raised_cr == 300
    assert p.num_rounds == 2

def test_company_latest_round():
    t = DealTracker()
    t.add(mk(company="X", amount=100, d=date(2023, 1, 1)))
    t.add(mk(company="X", amount=200, d=date(2025, 1, 1)))
    p = t.company_profile("X")
    assert p.latest_round.amount_cr == 200

def test_company_valuation_step_up():
    t = DealTracker()
    t.add(mk(company="X", amount=50, pre=150, d=date(2023, 1, 1)))   # post 200
    t.add(mk(company="X", amount=100, pre=500, d=date(2024, 1, 1)))  # post 600
    p = t.company_profile("X")
    assert p.valuation_step_up() == pytest.approx(3.0)  # 600/200

def test_company_profile_missing():
    t = DealTracker()
    assert t.company_profile("Nope") is None

def test_companies_list():
    t = DealTracker()
    t.add(mk(company="A"))
    t.add(mk(company="B"))
    t.add(mk(company="A"))
    assert len(t.companies()) == 2


# ── Biggest rounds & averages ────────────────────────────────────────────────

def test_biggest_rounds():
    t = DealTracker()
    t.add(mk(company="Small", amount=10))
    t.add(mk(company="Big", amount=1000))
    t.add(mk(company="Mid", amount=100))
    big = t.biggest_rounds(2)
    assert big[0].company == "Big"
    assert big[1].company == "Mid"

def test_average_round_size():
    t = DealTracker()
    t.add(mk(amount=100, stage=Stage.SEED))
    t.add(mk(amount=200, stage=Stage.SEED))
    assert t.average_round_size(stage=Stage.SEED) == 150

def test_average_round_size_empty():
    t = DealTracker()
    assert t.average_round_size() is None


# ── JSON loading ──────────────────────────────────────────────────────────────

def test_load_json(tmp_path):
    data = {"rounds": [
        {"company": "Agnikul", "sector": "Space Tech", "stage": "Series B",
         "amount_cr": 200, "date": "2024-05-01", "pre_money_cr": 800,
         "lead_investor": "Celesta", "city": "Chennai"},
        {"company": "Mindgrove", "sector": "Semiconductors", "stage": "Seed",
         "amount_cr": 75, "date": "2024-03-15", "lead_investor": "Peak XV"},
    ]}
    p = tmp_path / "deals.json"
    p.write_text(json.dumps(data))
    t = DealTracker()
    n = t.load_json(str(p))
    assert n == 2
    assert t.total_funding_cr == 275
    assert t.company_profile("Agnikul").latest_valuation_cr == 1000


def test_parse_date_formats():
    assert _parse_date("2025-06-01") == date(2025, 6, 1)
    assert _parse_date("01/06/2025") == date(2025, 6, 1)

def test_parse_date_invalid():
    with pytest.raises(ValueError):
        _parse_date("not-a-date")

def test_sector_from_key_fallback():
    assert _sector_from_key("totally unknown thing") == Sector.OTHER

def test_stage_from_key():
    assert _stage_from_key("Seed") == Stage.SEED
