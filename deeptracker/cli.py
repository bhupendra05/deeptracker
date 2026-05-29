"""CLI for DeepTracker."""
from __future__ import annotations
import click
from .tracker import DealTracker
from .models import Sector, Stage

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    console = Console()
    _RICH = True
except ImportError:
    console = None
    _RICH = False


def _cr(v): return f"₹{v:,.0f} Cr"


@click.group()
def cli():
    """DeepTracker — deep-tech funding & valuation analytics for Indian startups."""


@cli.command("report")
@click.argument("datafile", type=click.Path(exists=True))
def report_cmd(datafile):
    """Market overview from a deals JSON file."""
    t = DealTracker()
    n = t.load_json(datafile)
    if not _RICH:
        print(f"{n} deals · {_cr(t.total_funding_cr)} total")
        for sec, amt in t.funding_by_sector().items():
            print(f"  {sec}: {_cr(amt)}")
        return

    console.print(f"\n[bold cyan]DeepTracker[/] · {n} deals · "
                  f"[bold]{_cr(t.total_funding_cr)}[/] total funding\n")

    st = Table(title="Funding by Sector", box=box.SIMPLE_HEAVY)
    st.add_column("Sector", style="bold")
    st.add_column("Funding", justify="right")
    st.add_column("Share", justify="right")
    for sec, amt in t.funding_by_sector().items():
        share = amt / t.total_funding_cr * 100 if t.total_funding_cr else 0
        st.add_row(sec, _cr(amt), f"{share:.1f}%")
    console.print(st)

    qt = Table(title="Funding by Quarter", box=box.SIMPLE_HEAVY)
    qt.add_column("Quarter", style="bold")
    qt.add_column("Funding", justify="right")
    qt.add_column("Deals", justify="right")
    for q, amt in t.funding_by_quarter().items():
        deals = len([r for r in t.rounds if r.quarter == q])
        qt.add_row(q, _cr(amt), str(deals))
    console.print(qt)

    it = Table(title="Most Active Investors", box=box.SIMPLE_HEAVY)
    it.add_column("Investor", style="bold")
    it.add_column("Deals", justify="right")
    for inv, cnt in t.top_investors(10):
        it.add_row(inv, str(cnt))
    console.print(it)


@cli.command("biggest")
@click.argument("datafile", type=click.Path(exists=True))
@click.option("-n", default=10, help="Number of rounds")
def biggest_cmd(datafile, n):
    """Show the biggest funding rounds."""
    t = DealTracker()
    t.load_json(datafile)
    if not _RICH:
        for r in t.biggest_rounds(n):
            print(f"{r.company}: {_cr(r.amount_cr)} ({r.stage.value}, {r.quarter})")
        return
    tbl = Table(title=f"Top {n} Rounds", box=box.SIMPLE_HEAVY)
    tbl.add_column("Company", style="bold")
    tbl.add_column("Amount", justify="right")
    tbl.add_column("Stage")
    tbl.add_column("Sector")
    tbl.add_column("Date")
    tbl.add_column("Lead Investor")
    for r in t.biggest_rounds(n):
        tbl.add_row(r.company, _cr(r.amount_cr), r.stage.value, r.sector.value,
                    str(r.date), r.lead_investor or "—")
    console.print(tbl)


@cli.command("company")
@click.argument("datafile", type=click.Path(exists=True))
@click.argument("name")
def company_cmd(datafile, name):
    """Show a single company's funding history."""
    t = DealTracker()
    t.load_json(datafile)
    p = t.company_profile(name)
    if not p:
        click.echo(f"No deals found for '{name}'")
        return
    if not _RICH:
        print(f"{p.name}: {_cr(p.total_raised_cr)} across {p.num_rounds} rounds")
        return
    console.print(f"\n[bold cyan]{p.name}[/] · {p.sector.value}")
    console.print(f"Total raised: [bold]{_cr(p.total_raised_cr)}[/] across "
                  f"{p.num_rounds} rounds")
    if p.latest_valuation_cr:
        console.print(f"Latest valuation: {_cr(p.latest_valuation_cr)}")
    if p.valuation_step_up():
        console.print(f"Last step-up: [green]{p.valuation_step_up():.2f}x[/]")
    tbl = Table(box=box.SIMPLE_HEAVY)
    tbl.add_column("Round")
    tbl.add_column("Amount", justify="right")
    tbl.add_column("Post-Money", justify="right")
    tbl.add_column("Date")
    tbl.add_column("Lead")
    for r in sorted(p.rounds, key=lambda r: r.date):
        pm = _cr(r.post_money_cr) if r.post_money_cr else "—"
        tbl.add_row(r.stage.value, _cr(r.amount_cr), pm, str(r.date), r.lead_investor or "—")
    console.print(tbl)


@cli.command("sectors")
def sectors_cmd():
    """List tracked deep-tech sectors and stages."""
    click.echo("Sectors: " + ", ".join(s.value for s in Sector))
    click.echo("Stages:  " + ", ".join(s.value for s in Stage))


def main():
    cli()
