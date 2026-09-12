# My PSE Portfolio

Personal dashboard: PSE account summary (buying power, portfolio value,
current stocks value) + historical PSE daily stock data, viewable from any
device via GitHub Pages.

## Layout

```
index.html                       # the page you open on your phone
accounts/PSE/account-details.json  # buying power / portfolio value (committed, public)
data/PSE/csv/Data_YYYY-MM-DD.txt   # historical daily PSE data (committed, public)
data/PSE/manifest.json             # list of available dates, used by index.html
data/PSE/tickers/<SYMBOL>.json     # per-ticker price history, used by the trend chart
data/PSE/tickers/manifest.json     # list of known symbols, used for autocomplete
data/PSE/screener.json             # precomputed momentum screener, used by the screener section
data/PSE/company-names.json        # ticker -> company name, used by the ticker trend section
credentials/credentials.example.json  # template only (committed)
credentials/credentials.json          # your real broker login (gitignored, NEVER committed)
scripts/generate_manifest.py       # regenerates data/PSE/manifest.json after adding new data
scripts/build_ticker_data.py       # regenerates data/PSE/tickers/ after adding new data
scripts/build_momentum_screener.py # regenerates data/PSE/screener.json after adding new data
```

## Momentum Screener

The "Momentum Screener" section ranks liquid, currently-active PSE
tickers by historical closing-price % change over daily/weekly/monthly/
quarterly windows, showing the top 5 movers per window with the exact
numbers behind each (start/end price, dates, average daily turnover).

**This is not financial advice or a prediction** — it's a plain,
disclosed calculation over the data already in this repo
(`scripts/build_momentum_screener.py`), filtered so thinly-traded or
stale names don't dominate the list just because of a single odd trade.
Past performance does not indicate future results.

## PSE Daily Data

Shows, for the selected date: **Most Active** (top 15 by peso value
traded), **Today's Winners** (top 10 gainers by %), and **Today's
Losers** (top 10 decliners by %). Tap any symbol to jump to its trend
chart.

## Ticker Trend

Search a symbol under "Ticker Trend" on the page (or tap any symbol
anywhere on the page) to see its price history: company name, a line
chart, period high/low, and % change over 1M/6M/1Y/5Y/ALL ranges. This is
powered by `data/PSE/tickers/<SYMBOL>.json`, built from every daily file
by `scripts/build_ticker_data.py` — one JSON file per ticker instead of
the page having to scan all 1800+ daily files.

Company names come from `data/PSE/company-names.json`, sourced once from
a public PSE ticker listing (see git history for the source) and covers
the ~275 common/major PSE stocks. Obscure preferred-share series and
small-caps not in that source just show the bare ticker rather than a
guessed name. To add a name, edit `data/PSE/company-names.json` directly
(`"SYMBOL": "Company Name"`) and push — no rebuild script needed.

## ⚠️ Privacy note

This repo is **public** and the GitHub Pages site is reachable by anyone
with the URL (GitHub's free tier doesn't support login-gated private
Pages). Your buying power and portfolio value in
`accounts/PSE/account-details.json` will be visible to anyone who has the
link. Nothing links to it, so it's practically private — but don't post
the repo or site URL anywhere public, and treat the link like a password.

Your actual broker **credentials never leave this machine** —
`credentials/credentials.json` is listed in `.gitignore` and will never be
committed or pushed.

## One-time setup

1. Create the GitHub repo (github.com → **New repository** → name it, e.g.
   `pse-portfolio` → **Public** → do NOT initialize with a README/gitignore,
   since this directory already has one).

2. Connect this local directory to it:

   ```bash
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```

3. Enable GitHub Pages: repo → **Settings** → **Pages** → Source:
   **Deploy from a branch** → Branch: `main`, folder `/ (root)` → Save.

4. After a minute, your site is live at:

   ```
   https://<your-username>.github.io/<repo-name>/
   ```

   Open that on your phone (bookmark or add to home screen).

## Setting up your credentials locally (not pushed)

```bash
cp credentials/credentials.example.json credentials/credentials.json
# edit credentials/credentials.json with your real broker login
```

## Updating your account details

Edit `accounts/PSE/account-details.json` with current numbers, then:

```bash
git add accounts/PSE/account-details.json
git commit -m "Update account details"
git push
```

The site picks up the change within a minute or two of GitHub Pages
rebuilding.

## Adding new daily PSE data

Drop the new `Data_YYYY-MM-DD.txt` file(s) into `data/PSE/csv/`, then:

```bash
python3 scripts/generate_manifest.py
python3 scripts/build_ticker_data.py
python3 scripts/build_momentum_screener.py
git add data/PSE/csv data/PSE/manifest.json data/PSE/tickers data/PSE/screener.json
git commit -m "Add PSE data for <date(s)>"
git push
```

## Column mapping (best-effort)

Each data file is colon-delimited, one row per stock, no header. The
first 11 fields are used by the page as:

`Symbol : PrevClose : Last : Change : %Change : Open : High : Low : Value : Trades : Volume`

The remaining fields (shares outstanding, market cap, trading status,
board lot, 52-week range, etc.) exist in the raw files but aren't
rendered by `index.html` — adjust the `renderRows()` function in
`index.html` if you want to surface more columns.
