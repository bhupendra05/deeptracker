# DeepTracker 🛰️

**Deep-tech funding round & valuation tracker for Indian startups.**

Track and analyze funding across India's deep-tech sectors — **semiconductors, space tech, aerospace & defence, eVTOL, biotech, quantum, robotics** — the sectors generic startup databases barely cover.

```bash
deeptracker report deals.json
deeptracker biggest deals.json -n 10
deeptracker company deals.json "Agnikul"
```

## What it answers

- 💰 How much capital flowed into **semiconductors** this quarter?
- 📈 Which sector is heating up fastest, quarter over quarter?
- 🏆 Who are the **most active deep-tech investors** in India?
- 🚀 What was **Company X's** valuation step-up between rounds?
- 📊 What are the **biggest rounds** of the year?

## Data format (JSON)

```json
{
  "rounds": [
    {
      "company": "Agnikul Cosmos",
      "sector": "Space Tech",
      "stage": "Series B",
      "amount_cr": 200,
      "date": "2024-05-01",
      "pre_money_cr": 800,
      "lead_investor": "Celesta Capital",
      "investors": ["Mayfield", "Pi Ventures"],
      "city": "Chennai"
    }
  ]
}
```

## Python API

```python
from deeptracker import DealTracker, Sector, Stage

t = DealTracker()
t.load_json("deals.json")

# Market overview
print(t.total_funding_cr)                 # total ₹ Cr tracked
print(t.funding_by_sector())              # {"Semiconductors": 1240, ...}
print(t.funding_by_quarter())             # quarterly trend
print(t.top_investors(10))                # most active investors

# Filter
space_deals = t.filter(sector=Sector.SPACE_TECH, year=2025, min_amount_cr=50)

# Company deep-dive
p = t.company_profile("Agnikul Cosmos")
print(p.total_raised_cr, p.latest_valuation_cr, p.valuation_step_up())
```

## Tracked sectors

`Semiconductors` · `Space Tech` · `Aerospace & Defence` · `eVTOL & Drones` ·
`Biotech & Life Sciences` · `AI / ML Infrastructure` · `Quantum Computing` ·
`Cleantech & Energy` · `Robotics`

## Commands

| Command | Purpose |
|---------|---------|
| `deeptracker report <file>` | Sector / quarter / investor overview |
| `deeptracker biggest <file> -n N` | Largest rounds |
| `deeptracker company <file> <name>` | Single company funding history |
| `deeptracker sectors` | List tracked sectors & stages |

---

© 2026 Bhupendra Gurjar. All rights reserved. Commercial / subscription license.
