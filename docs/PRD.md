# PandaLedger — Product Requirements Document

**Status:** Draft v1 — pending sign-off on items flagged 🔶
**Owner:** Python Panda Studios
**Target runtime:** Python 3.12+
**Repo:** github.com/PythonPandaStudios/PandaLedger

---

## 1. Vision

PandaLedger is a local-first personal budgeting and payroll-forecasting desktop app. A user imports
their bank/credit statements, the app learns how to categorize their spending, builds a monthly budget
around a strategy the user picks, estimates what their next paycheck will actually deposit after real
tax withholding, and tells them how much they can safely save. No data leaves the user's machine in v1.

This is a ground-up rewrite of the existing PySide6 prototype. The payroll math and SQLAlchemy/SQLite
storage approach are worth keeping conceptually; the UI toolkit, packaging pipeline, and several
correctness gaps in the tax engine are not.

## 2. Scope Summary

| # | System | v1 | v2 | v3 / later |
|---|---|---|---|---|
| 1 | UI shell (Toga, light/dark) | ✅ | extend for mobile | — |
| 2 | Statement import (CSV/QFX/QBO, column mapping, dedupe) | ✅ | + PDF | — |
| 3 | Auto-categorization (rule engine) | ✅ | smarter suggestions | — |
| 4 | Manual transactions (add/edit/delete/split/recurring) | ✅ | — | — |
| 5 | Monthly budget suggestions (strategy-driven) | ✅ | — | — |
| 6 | Monthly budget (category caps, custom categories) | ✅ | — | — |
| 7 | Savings recommendations (strategy-driven) | ✅ | — | — |
| 8 | Paycheck estimator (real bracket withholding, multi-job) | ✅ | — | — |
| 9 | Receipt attachments | — | ✅ | — |
| 10 | Multi-device sync | — | ✅ (LAN) | ✅ (remote) |
| 11 | Android app | — | ✅ | — |
| 12 | iOS app | — | — | maybe |
| 13 | Live bank connections (Plaid/etc.) | ❌ not planned | ❌ | 🔶 undecided |

## 3. Technology Stack

- **Language:** Python 3.12+
- **UI toolkit:** [Toga](https://toga.readthedocs.io) (BeeWare). Chosen over PySide6 because the packaging
  target is Briefcase, and Briefcase's Android/iOS story is built around Toga; the Qt backend for Toga has
  also matured a lot recently (Table/Tree/Canvas/dialogs are now solid on the Qt/GTK/WinForms backends).
  🔶 **Trade-off you're accepting:** Toga's widgets are simpler than raw Qt — no built-in charting widget,
  more basic tables. Plan on either a Toga `Canvas`-drawn chart or a small bundled charting helper for the
  dashboard, and expect some UI polish work that would've been "free" in Qt.
- **Packaging:** [Briefcase](https://briefcase.readthedocs.io) — builds the Linux Mint (.deb/AppImage)
  target now, Android later.
- **Dependency management:** [Poetry](https://python-poetry.org) 2.x, using the PEP 621 `[project]` table
  (not the legacy `[tool.poetry.dependencies]` format) so the same `pyproject.toml` metadata is readable by
  Briefcase directly. Poetry-specific extras (lockfile, dev-dependency groups) live under `[tool.poetry]`
  alongside it. **Verify at setup time** that the installed Briefcase version reads `[project.dependencies]`
  cleanly for your Toga template version — this integration is still evolving upstream.
- **ORM / storage:** SQLAlchemy 2.x + SQLite (one file per user, same as today).
- **Testing:** pytest.
- **Lint/format:** ruff (replaces flake8+black+isort in one tool).
- **Type checking:** mypy in strict mode. (ty, Astral's newer type checker, is promising but pre-1.0 as of
  early 2026 — stick with mypy for a production app until it stabilizes further; revisit later.)
- **CI:** GitHub Actions — lint, type-check, test on every PR; build artifacts on tag (see §10.4).

## 4. Platform Targets

- **v1:** Linux Mint (your daily driver), built/tested as a Debian-family `.deb` via Briefcase. Cinnamon
  desktop theme quirks (GTK-based) should be checked explicitly since Toga's Linux backend is GTK.
- **v2:** Android (Briefcase's Android template; BeeWare has been actively landing NumPy/Pandas/SciPy
  Android wheel support, so a future move to Pandas for reporting stays on the table).
- **v3+:** iOS — explicitly deprioritized, revisit only if you get an iOS device or outside demand shows up.

## 5. Architecture

Keep a Model-View-Controller-ish split, adapted to Toga idioms:

```
pandaledger/
├── pyproject.toml              # PEP 621 [project] + [tool.poetry] + [tool.briefcase]
├── src/
│   └── pandaledger/
│       ├── __main__.py
│       ├── app.py              # Toga App subclass, wires everything together
│       ├── controllers/        # Application logic, one module per feature area
│       │   ├── import_controller.py
│       │   ├── categorization_controller.py
│       │   ├── transaction_controller.py
│       │   ├── budget_controller.py
│       │   ├── savings_controller.py
│       │   └── payroll_controller.py
│       ├── models/              # SQLAlchemy schema + pure business logic (no Toga imports here)
│       │   ├── schema.py
│       │   ├── database.py
│       │   ├── payroll/
│       │   │   ├── federal.py   # Percentage-method engine, reads tax_tables/federal/*.json
│       │   │   ├── state.py     # State bracket engine, reads tax_tables/state/*.json
│       │   │   └── fica.py
│       │   ├── categorization.py
│       │   ├── budgeting/       # one module per strategy (see §7.5)
│       │   └── savings/         # one module per strategy (see §7.7)
│       ├── importers/           # one module per file format
│       │   ├── csv_importer.py
│       │   ├── qfx_importer.py
│       │   └── qbo_importer.py
│       ├── views/               # Toga widgets/boxes, one module per screen
│       ├── resources/
│       │   └── tax_tables/      # versioned JSON data, NOT hardcoded in .py — see §7.8
│       └── sync/                # v2 — stubbed out, not built in v1 (see §9.2)
└── tests/
```

Rule of thumb carried over from the old `GEMINI.md`: `models/` and `importers/` must stay free of any
`toga.*` imports, so business logic is testable headlessly and reusable if the UI layer ever changes again.

## 6. Data Model

Core correctness change from the current schema: **money moves from `Float` to integer cents
(`Column(Integer)`, stored as whole cents) or `Numeric`/`Decimal`.** The existing schema stores dollars as
`Float`, which silently accumulates rounding error in any budgeting or tax app — this must not carry into
the rewrite. All amounts below are `int` cents unless noted.

```
Institution        id, name, kind (bank/credit_union/broker), notes

Account            id, institution_id → Institution, name, type (checking/savings/credit),
                   current_balance_cents, import_column_map_id → ImportColumnMap (nullable)

ImportColumnMap     id, institution_id → Institution (nullable = generic), file_format (csv/qfx/qbo),
                   column_mapping (JSON: which source column → date/payee/amount/etc.)

ImportBatch         id, account_id → Account, imported_at, source_filename, row_count,
                   duplicate_count (for the import summary screen)

Category            id, name, type (Fixed/Variable/Savings), user_created (bool),
                   monthly_limit_cents, parent_category_id (nullable, for sub-categories)

CategorizationRule  id, pattern (string), match_type (substring/regex), category_id → Category,
                   priority (int, first match wins), auto_apply (bool), created_from_transaction_id
                   (nullable, so the UI can show "learned from this transaction")

Transaction         id, account_id → Account, date, payee, amount_cents, notes,
                   category_id → Category (nullable until categorized),
                   import_batch_id → ImportBatch (nullable — manual entries have none),
                   dedupe_hash (unique per account — see §7.2),
                   external_txn_id (QFX/QBO FITID when available, else null),
                   parent_transaction_id (nullable — set on both rows of a split),
                   is_pending_review (bool — categorized by a fuzzy rule, awaiting user OK)

RecurringTransaction id, account_id, category_id, payee, amount_cents, frequency
                   (weekly/biweekly/monthly/etc.), next_due_date, last_generated_date

IncomeSource         id, name (e.g. "Commdex", "Blue Mountain Radios"), income_type (hourly/salary),
                   rate_cents, schedule (weekly/biweekly/semi_monthly/monthly), schedule_config (JSON —
                   the day-of-month fields the current PayrollCalculator already models),
                   filing_status, state_code

Deduction            id, income_source_id → IncomeSource, name, amount_cents_or_percent, is_percent,
                   is_pre_tax, category (401k/HSA/insurance/Roth/other)

BudgetPlan           id, month, year, strategy (zero_based/fifty_thirty_twenty/rolling_average),
                   strategy_config (JSON)

BudgetLine           id, budget_plan_id → BudgetPlan, category_id → Category, suggested_cents,
                   approved_cents (user can override the suggestion)

SavingsGoal          id, strategy (pay_yourself_first/emergency_fund/leftover_sweep), strategy_config
                   (JSON — e.g. target months of expenses, target date, fixed %), target_cents,
                   current_cents

Config               key, value   (kept as-is — theme, active strategy IDs, etc.)
```

Two forward-looking fields belong in the schema **now**, even though sync is v2, because retrofitting them
later means a painful migration: every table above gets a `uuid` primary/alternate key and an
`updated_at` timestamp, and deletes are soft (`deleted_at` timestamp) instead of row-removal. This costs
almost nothing today and is the difference between "sync is a schema migration" and "sync is a rewrite" in
v2 (see §9.2).

## 7. Feature Specifications

### 7.1 UI Shell
- Toga `MainWindow` with a persistent left-nav (Dashboard / Transactions / Budget / Savings / Paycheck /
  Import / Settings) — mirrors typical Toga app-shell patterns.
- Light/dark theme carried over from the existing `theme_manager.py` concept, redone as Toga style
  definitions rather than Qt stylesheets.
- Dashboard: current-month budget-vs-actual, next paycheck estimate, savings goal progress. Charts drawn
  on a Toga `Canvas` (bar/line, hand-rolled — no charting library dependency needed for v1's simple needs).
- First-run setup wizard: create first Account → pick Budget strategy → pick Savings strategy → (optional)
  set up first IncomeSource. This wizard is where the strategy choice from §7.5/§7.7 happens.

### 7.2 Statement Import
- Formats: **CSV, QFX (Quicken), QBO (Quicken/QuickBooks Web Connect)** for v1. PDF explicitly deferred to
  v2/v3 (PDF bank statements are unstructured and require per-bank layout parsing — much higher effort for
  low marginal value once QFX/CSV cover Capital One).
- QFX/QBO both carry a bank-assigned `FITID` per transaction (OFX spec) — use that as the dedupe key
  whenever it's present; it's far more reliable than any heuristic.
- CSV has no such ID, so dedupe falls back to a hash of `(account_id, date, amount_cents, payee,
  running_balance_if_present)`. Store this as `Transaction.dedupe_hash` with a unique constraint per
  account, so re-importing the same statement (or an overlapping date range from a second export) is a
  no-op rather than a duplicate.
- **Column mapping is required, not optional**, per your answer — build a mapping UI (pick which source
  column is date/payee/amount/etc., save it per `Institution` so Capital One only needs to be mapped once).
  This is what makes credit-card imports and other users' banks work without code changes.
- Post-import summary screen: "Imported 42 transactions, skipped 5 duplicates, 3 need a category" — this
  is also where newly-imported transactions enter the categorization review queue (§7.3).

### 7.3 Auto-Categorization
- Rule engine, not ML: user-defined rules of `(pattern, match_type: substring|regex) → category`, evaluated
  in priority order, first match wins.
- Rules can be created two ways: explicitly in a "Manage Rules" screen, or implicitly — when a user
  manually categorizes an uncategorized transaction, offer "always categorize `{payee}` as `{category}`
  going forward?" which creates a substring rule from that payee.
- Two modes per rule (your answer): `auto_apply=True` commits the category immediately on import;
  `auto_apply=False` marks the transaction `is_pending_review=True` and it shows in a review queue where
  the user approves/rejects/reassigns before it's final. Default new rules to review-required; let the user
  flip a rule to auto-apply once they trust it.

### 7.4 Manual Transactions
- Full CRUD, plus:
  - **Split:** one statement line → two-or-more `Transaction` rows sharing `parent_transaction_id`, whose
    `amount_cents` sum to the original; the original import row's amount is preserved on the parent for
    reconciliation, children carry the category-specific split amounts.
  - **Recurring:** `RecurringTransaction` generates a projected `Transaction` on its `next_due_date`
    (useful for forward-looking budget math even before the real statement line arrives), then reconciles
    with the real imported transaction when it shows up (matched by account + payee + approximate amount +
    date window) rather than double-counting it.

### 7.5 Monthly Budget Suggestions & 7.6 Monthly Budget
Per your answer, the budget *strategy* is a first-run choice, changeable anytime. Three strategies for v1
🔶 (proposed — say the word if you'd rather swap one out):

1. **Rolling Average** — suggested cap per category = trailing N-month (default 3, configurable) average
   spend in that category. Simplest, "learn from your own habits," good default for a first-time user with
   import history but no budgeting experience yet.
2. **50/30/20 Rule** — Needs/Wants/Savings split of net income, using the *existing* `Category.type`
   enum (`Fixed`→Needs, `Variable`→Wants, `Savings`→Savings) that's already in the old schema — this
   strategy falls out almost for free from data you're already collecting.
3. **Zero-Based** — every dollar of the month's income gets assigned to a category (spending or savings)
   until the unallocated remainder is $0; suggestions pre-fill from the Rolling Average numbers as a
   starting point, but the *check* is that everything must be assigned.

`BudgetLine.suggested_cents` is machine-generated by whichever strategy is active; `approved_cents` is
what the user actually commits to (defaults to the suggestion, editable). Category limits are user-editable
and users can create their own categories (your answer) — categorization rules and budget lines both point
at the same `Category` table, so a new category is immediately usable in both places.
- Rollover: 🔶 needs a decision — does an unspent category balance carry into next month, or reset? Not
  blocking (I'll default to **reset, with an optional per-category "rollover" flag** unless you say
  otherwise) but flag it before this ships.

### 7.7 Savings Recommendations
Same "pick a strategy at setup, change anytime" pattern. Three strategies 🔶 (proposed):

1. **Pay-Yourself-First** — a fixed % or fixed $ of each paycheck (from §7.8) is recommended as a transfer
   to savings *before* the rest of the month is budgeted.
2. **Emergency Fund Target** — target = N months (default 3, user-configurable) of `Fixed`-category
   spending; the app shows progress toward that number and suggests a monthly contribution to hit a
   user-chosen target date.
3. **Leftover Sweep** — at month close, `income − actual spend` is surfaced as a suggested savings
   transfer. Reactive rather than proactive — good complement to the other two rather than a full
   replacement.

### 7.8 Paycheck / Payout Estimator
This is the biggest correctness upgrade over the existing prototype. Current code: flat user-entered
Fed/State %, no Social Security wage-base cap, no Additional Medicare Tax, single global pay config. New
design, per your answers (real bracket withholding, multiple concurrent jobs):

- **Federal:** IRS Publication 15-T "Percentage Method for Automated Payroll Systems." Annualize the wage
  for the period, subtract the standard deduction for filing status (no Form W-4 Step 4 support planned for
  v1 — flag if you want that), run it through the bracket table (`base_amount + rate × (annual_wage −
  bracket_floor)`), divide back down to the period. Bracket tables are **data, not code** — stored as
  `resources/tax_tables/federal/2026.json` keyed by filing status and pay frequency, because the IRS
  reissues these every year. The app should refuse to guess a tax year's numbers it doesn't have a table
  for, and prompt the user to add one (or ship an update).
- **State:** Same bracket-table shape, one JSON file per state per year
  (`resources/tax_tables/state/<state>/2026.json`). No-income-tax states just get an empty/zero table.
  Pre-seed the states you can verify now; let users define/edit a state's brackets through a settings
  screen for anywhere not pre-seeded — 50 states of tax law is not something to hand-maintain accurately
  forever, so this needs to be user-editable data from day one, not a hardcoded lookup.
- **FICA, fixed by law, still worth encoding correctly:**
  - Social Security: 6.2%, **capped at the annual wage base** ($184,500 for 2026 — store as a yearly
    constant, not a hardcoded literal in the calculator).
  - Medicare: 1.45% on all wages, **plus Additional Medicare Tax of 0.9%** on wages above $200,000
    (single) / $250,000 (MFJ) / $125,000 (MFS) — the current calculator has neither the SS cap nor this
    surtax; both need to exist for the numbers to be honest at higher incomes.
- **Multiple concurrent income sources:** each `IncomeSource` runs its own schedule/withholding
  independently (this is actually simpler than trying to combine jobs into one calculation, and matches
  how W-4 multi-job math is genuinely complicated to get right jointly — v1 treats each job's federal
  withholding independently, which is the same simplification most paycheck calculators make; flag if you
  specifically need the "Step 2 multiple jobs" combined-withholding adjustment from the W-4 worksheet).
  Yearly/monthly overview screens then aggregate across all active `IncomeSource` rows.
- Deductions (pre-tax: 401k/HSA; post-tax: insurance/Roth) apply per-`IncomeSource` as today, pre-tax ones
  reducing taxable income before the bracket calculation.

## 8. Non-Functional Requirements

- **Privacy/security:** All financial data stays local in v1 — no network calls anywhere in `models/` or
  `importers/`. SQLite file lives in the platform's standard app-data location (same pattern as today).
  🔶 Worth deciding now: do you want the SQLite file encrypted at rest (e.g. SQLCipher) given it's real
  bank data? Not required for v1 to function, but cheap to add now vs. retrofit later.
- **Testing:** Every `models/` and `importers/` module needs unit tests; `pytest` must pass before any
  merge (enforced by CI, see §10.4 and `CLAUDE.md`). Tax-bracket math especially needs table-driven tests
  against known IRS worked examples, not just internal consistency checks.
- **Docstrings/comments:** Google-style docstrings on every class and method; inline comments required on
  any non-obvious logic (bracket math, dedupe hashing, split-transaction reconciliation, recurring-vs-real
  matching) — this is a hard requirement per your original ask, also encoded in `CLAUDE.md`.
- **No placeholder code:** no `# TODO`, no `...`, no "implement later" stubs merged to `dev` or `main`.

## 9. V2 / V3 Roadmap

### 9.1 Receipt Attachments
Revive the `receipt_path`-style field from the current schema (dropped from v1 scope per your answer).
Straightforward: attach a file path (or later, embed the image) to a `Transaction`.

### 9.2 Multi-Device Sync — needs more design work before it's buildable
You flagged this one yourself as needing more thought, so here's a starting proposal rather than a final
answer:

**Recommended direction: journaled changes distributed through a folder you already sync, not a
custom client/server protocol.** Concretely: every write to the local database also appends a small
signed/encrypted change record (table, row uuid, changed fields, `updated_at`) to a local "outbox" file.
That outbox lives inside a folder you point at a sync tool of your choosing — Syncthing for pure LAN-only
sync with zero third parties involved, or a Dropbox/OneDrive-style folder later if you want it to reach a
phone over the internet without you standing up your own server. On startup, each device replays any new
change records it hasn't seen yet into its local SQLite copy, using `updated_at` for last-write-wins and
the `deleted_at` soft-delete column (§6) so a delete on one device doesn't get "resurrected" by an update
racing in from another.

Why this over a LAN discovery/server approach: it needs no networking code running inside the app at all
(no open ports, no mDNS/zeroconf discovery to build and secure), it's the same mechanism whether the two
devices are on your home LAN or one of them is a phone on cellular data months from now, and "local" can
still mean *fully* local if you pick Syncthing as the transport — no cloud company ever touches the data.
The trade-off is it's not real-time (sync happens on the sync tool's schedule, not instantly), which seems
fine for a personal budget app.

This needs a real design pass before implementation — flagging as the plan going in, not locking it in.

### 9.3 Android
Once Toga's Android backend covers what the v1 UI needs, Briefcase can target it from the same codebase.
Revisit sync design (9.2) with "phone on cellular, not LAN" as a first-class case before this ships, since
it changes which sync transport actually works.

## 10. Development Process

### 10.1 Repo Cleanup (do this first, before any new code)
Remove Gemini-specific artifacts found in the current repo:
- `GEMINI.md` → replaced by `CLAUDE.md`
- `.geminiignore`
- `gemini.codeAssist.*` / `geminicodeassist.*` keys in `.vscode/settings.json`

### 10.2 Branching Model (per your answer)
- One feature branch per system/feature (e.g. `feature/statement-import`, `feature/paycheck-estimator`).
- Feature branches PR into `dev`.
- `dev` merges to `main` only once everything on `dev` passes CI and has been manually verified.
- See `CLAUDE.md` for commit message and PR conventions.

### 10.3 Definition of Done (per feature)
- [ ] Google-style docstrings on all new classes/methods; complex logic commented
- [ ] Full type hints; `mypy` clean
- [ ] `ruff` clean (lint + format)
- [ ] Unit tests added/passing for anything in `models/` or `importers/`
- [ ] No `Float` used for money anywhere in the diff
- [ ] Manually tested on Linux Mint via `briefcase dev`

### 10.4 CI/CD
GitHub Actions: lint + type-check + test on every push/PR (replaces the current test-only workflow).
Release builds move from PyInstaller to `briefcase build` / `briefcase package` for the Linux target,
triggered on version tags, same as today's tag-triggered release pattern.

## 11. Open Items Needing Your Sign-Off

Collected from the 🔶 markers above, so nothing gets missed:
1. Budget strategies: Rolling Average / 50-30-20 / Zero-Based — OK as the v1 three, or swap one?
2. Savings strategies: Pay-Yourself-First / Emergency Fund / Leftover Sweep — OK as the v1 three?
3. Category rollover behavior — reset monthly, or carry unspent balance forward?
4. Encrypt the SQLite file at rest (e.g. SQLCipher) in v1, or defer?
5. W-4 Step 2 "multiple jobs" combined withholding adjustment — in scope for v1, or is per-job independent
   withholding good enough?
6. Sync direction (§9.2) — sound right as the v2 starting point?