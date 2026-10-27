# FIN 439 — Lab 16: Provenance Gate

**Student:** Ethan Heeres  
**Lab partner:** Aidan Murrin  
**Decision date:** March 31, 2026  
**Data:** Instructor's fictional one-year zero-coupon bond fund prices (AAA, BBB, CCC)  
**Source:** Training table supplied for Lab 16; no external market data

## Run the filter

From this folder, run:

```bash
python asof.py
```

On Windows, `py asof.py` also works if `python` is not recognized. The script uses only the Python standard library. Change `DECISION_DATE` at the top of `asof.py` to test another date.

## D — Question

On the date I would have traded, what did the data actually say, and how much of what I see now came later?

The **month measured** is when the price applies; the **published-on date** is when it became available. Even a February observation cannot be used for a March 31 trade if it was not published until April. If February is revised, I can use only the version published by the decision date.

## R / I — Row funnel

The script applies the four rules **in the assigned order**. It preserves the original row IDs throughout.

| Rule | Outcome | Row IDs |
| --- | --- | --- |
| 1. Quarantine missing ticker | 1 quarantined | 11 |
| 2. Remove exact duplicate | 1 removed | 7 |
| 3. Remove publication after March 31 | 3 removed | 3, 8, 10 |
| 4. Keep latest available ticker/month vintage | 1 replaced | 2 |
| **Final as-of panel** | **6 rows kept** | **1, 4, 5, 6, 9, 12** |

The duplicate check compares ticker, month, publication date and price, not the unique row number. The fourth rule keeps row 4 instead of row 2: AAA's February price was revised from 104.0 to 103.0 on March 25, before the decision date.

### As-of panel

| Row | Ticker | Measured month | Published on | Price |
| --- | --- | --- | --- | ---: |
| 1 | AAA | 2026-01 | 2026-02-10 | 101.0 |
| 4 | AAA | 2026-02 | 2026-03-25 | 103.0 |
| 5 | BBB | 2026-01 | 2026-02-10 | 98.0 |
| 6 | BBB | 2026-02 | 2026-03-10 | 97.0 |
| 9 | CCC | 2026-01 | 2026-02-10 | 110.0 |
| 12 | CCC | 2026-02 | 2026-03-10 | 111.0 |

### Signals: latest measured month versus previous month

The signal is `(latest price / previous month's price - 1) * 100`. The **naive** result keeps the latest publication for every ticker/month, even when it was published after March 31.

| Ticker | As-of signal | Naive signal |
| --- | --- | --- |
| AAA | +1.98% (February: 103 / 101 - 1) | +5.83% (March: 109 / 103 - 1) |
| BBB | -1.02% (February: 97 / 98 - 1) | -5.15% (March: 92 / 97 - 1) |
| CCC | +0.91% (February: 111 / 110 - 1) | +1.82% (February revised: 112 / 110 - 1) |

**All four funnel steps, the six remaining rows, and the six signals match the instructor's known answer.**

## V — Sanity check by hand

For these one-year zero-coupon bonds, yield is `100 / price - 1`. These calculations use the as-of panel, not the later data.

| Row | Fund | Month | Price | Yield | What it breaks |
| --- | --- | --- | ---: | ---: | --- |
| 1 | AAA | Jan | 101.0 | -0.99% | Negative yield |
| 4 | AAA | Feb | 103.0 | -2.91% | Negative yield |
| 5 | BBB | Jan | 98.0 | +2.04% | Nothing |
| 6 | BBB | Feb | 97.0 | +3.09% | Nothing |
| 9 | CCC | Jan | 110.0 | -9.09% | Negative yield; priced above AAA and BBB |
| 12 | CCC | Feb | 111.0 | -9.91% | Negative yield; priced above AAA and BBB |

The date gate passed these six rows, but four prices still fail the exercise's sanity expectations. In this exercise, the fifth rule would **quarantine any price over 100 (negative yield)**, which would catch rows 1, 4, 9 and 12. A separate credit-order check should flag cases where CCC is priced above BBB or AAA at the same maturity. Negative yields can exist in real markets, so a price-over-100 prohibition is an assumption for this particular training example, not a universal market rule.

## Date-shift check

Setting `DECISION_DATE = "2026-04-15"` admits the later March publications and CCC's later February revision. The **as-of** signals then equal the **naive** signals for all three funds:

| Ticker | As-of at April 15 | Naive |
| --- | ---: | ---: |
| AAA | +5.83% | +5.83% |
| BBB | -5.15% | -5.15% |
| CCC | +1.82% | +1.82% |

After the check, restore `DECISION_DATE = "2026-03-31"`. This date-shift test was run on this script; running the separate partner's file still requires that file.

## Learn — point-in-time

1. **Look-ahead bias** is using information in a historical decision or backtest that was not available at the time.
2. The **event time** tells me the month measured. The **publication time** determines when I could actually use it. A **revision** can change an earlier month's value, but I cannot use it before that revised version is released.
3. AAA is the clearest example. On March 31, the latest knowable price was February's revised 103.0, giving +1.98% against January's 101.0. The naive +5.83% uses a March price of 109.0 that was not published until April 10. That March return could not have informed my March 31 trade.

## Reflect

1. **Most important removal:** Rule 3 removed AAA row 3, the March price published April 10. Including it would inflate the as-of AAA signal from +1.98% to +5.83%. Rule 4 also matters: without replacing row 2 with row 4, AAA's February return would incorrectly be +2.97%.
2. **Naive backtest:** It would act as though I could trade using the April releases and the later CCC revision on March 31. It would overstate how much information the strategy actually had. Whether that improves reported performance depends on the trading rule, but the test would not be realistic.
3. **Fifth rule:** In the given training assumptions, quarantine any one-year zero-coupon price above its 100 face value, which catches exactly rows 1, 4, 9 and 12. I would also review relative prices by credit rating, because a riskier CCC bond should generally be cheaper than the BBB and AAA bonds at the same maturity.

## Explain the code / partner activity

In `latest_vintages`, `key = (ticker, month)` groups versions of the same observation. `old = latest.get(key)` finds the version kept so far. If no version exists, or a new row has a later publication date, `latest[key] = row` keeps the newer version. The row numbers remain intact, so the funnel can report which older version was replaced. A same-date tie is broken by row number for deterministic output.

### Partner discussion — Aidan Murrin

Aidan and I discussed how the publication date controls what is available for a trading decision, and why a revised row can replace an older version of the same month. I explained that **our as-of filter is designed to prevent look-ahead bias**, while the naive results are calculated separately to illustrate the effect of using later information. We also discussed the distinction between provenance gating and keeping training and test sets separate.

**Code question discussed:** Why use AAA row 4 rather than row 2? Both measure February, but row 4 was published March 25, later than row 2 on March 10, and both were knowable by March 31. The newer revision gives +1.98% rather than +2.97%.

We also worked through why row 3 cannot be used on March 31 (published April 10) and why it *would* be allowed for an April 15 decision. The date-shift calculation was verified using my `asof.py`; I have not recorded a separate run of Aidan's file.

## Checkout

Submit the GitHub links to this `README.md` and `asof.py` after uploading them to your chosen repository. No files are automatically published to GitHub from this package.

For Thursday, the same gate can be used with a monthly ALFRED series and its publication vintages. Its source, units, publication lags, revisions and download date should be recorded separately.
