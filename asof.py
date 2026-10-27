"""FIN 439 Lab 16: point-in-time provenance gate (standard library only)."""

from collections import defaultdict
from datetime import date

# Editable inputs: change this date to 2026-04-15 for the partner test.
DECISION_DATE = "2026-03-31"

# Row number, ticker, month measured, date published, and price.
TABLE = [
    (1, "AAA", "2026-01", "2026-02-10", 101.0),
    (2, "AAA", "2026-02", "2026-03-10", 104.0),
    (3, "AAA", "2026-03", "2026-04-10", 109.0),
    (4, "AAA", "2026-02", "2026-03-25", 103.0),
    (5, "BBB", "2026-01", "2026-02-10", 98.0),
    (6, "BBB", "2026-02", "2026-03-10", 97.0),
    (7, "BBB", "2026-02", "2026-03-10", 97.0),
    (8, "BBB", "2026-03", "2026-04-10", 92.0),
    (9, "CCC", "2026-01", "2026-02-10", 110.0),
    (10, "CCC", "2026-02", "2026-04-05", 112.0),
    (11, "", "2026-02", "2026-03-10", 99.0),
    (12, "CCC", "2026-02", "2026-03-10", 111.0),
]


def latest_vintages(rows):
    """Keep the newest published row for each ticker and measured month."""
    latest = {}
    for row in rows:
        row_id, ticker, month, published, price = row
        key = (ticker, month)
        old = latest.get(key)
        if old is None or (published, row_id) > (old[3], old[0]):
            latest[key] = row

    kept = sorted(latest.values(), key=lambda r: (r[1], r[2]))
    removed = sorted(r[0] for r in rows if latest[(r[1], r[2])][0] != r[0])
    return kept, removed


def signals(rows):
    """Change in price between each ticker's two latest measured months."""
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row[1]].append(row)

    result = {}
    for ticker, prices in by_ticker.items():
        prices.sort(key=lambda r: r[2])
        if len(prices) < 2:
            result[ticker] = None
        else:
            previous, latest = prices[-2], prices[-1]
            result[ticker] = ((latest[4] / previous[4] - 1) * 100, latest[2])
    return result


def display_signal(value):
    if value is None:
        return "N/A (fewer than two months)"
    pct, month = value
    return f"{pct:+.2f}% ({month})"


def main():
    decision_date = date.fromisoformat(DECISION_DATE)

    # Rule 1: quarantine missing tickers.
    quarantined = [r[0] for r in TABLE if not r[1].strip()]
    named = [r for r in TABLE if r[1].strip()]

    # Rule 2: remove exact duplicates (excluding the unique source row number).
    seen = set()
    unique = []
    duplicates = []
    for row in named:
        record = row[1:]
        if record in seen:
            duplicates.append(row[0])
        else:
            seen.add(record)
            unique.append(row)

    # Rule 3: remove records first published after the decision date.
    late = [r[0] for r in unique if date.fromisoformat(r[3]) > decision_date]
    on_time = [r for r in unique if date.fromisoformat(r[3]) <= decision_date]

    # Rule 4: keep only the latest available publication for each ticker/month.
    panel, replaced = latest_vintages(on_time)

    # Naive comparison: same nonmissing/deduplicated data but NO date cutoff.
    naive_panel, _ = latest_vintages(unique)
    asof_signals = signals(panel)
    naive_signals = signals(naive_panel)

    print(f"ROW FUNNEL (decision date: {DECISION_DATE})")
    for label, ids in [
        ("1. Quarantined (missing ticker)", quarantined),
        ("2. Removed (exact duplicate)", duplicates),
        ("3. Removed (published after decision date)", late),
        ("4. Removed (superseded vintage)", replaced),
    ]:
        print(f"{label}: {len(ids)} row(s): {sorted(ids)}")

    print(f"\nAS-OF PANEL ({len(panel)} rows)")
    print(f"{'Row':<5}{'Ticker':<9}{'Month':<11}{'Published':<14}{'Price':>7}")
    for row_id, ticker, month, published, price in panel:
        print(f"{row_id:<5}{ticker:<9}{month:<11}{published:<14}{price:>7.1f}")

    print("\nPRICE CHANGE SIGNALS")
    print(f"{'Ticker':<9}{'As-of':<25}Naive (ignores release date)")
    for ticker in sorted(asof_signals):
        print(f"{ticker:<9}{display_signal(asof_signals[ticker]):<25}"
              f"{display_signal(naive_signals[ticker])}")


if __name__ == "__main__":
    main()
