# Jyotish App

Jyotish App is a free, open source web application for Vedic astrology (Jyotish). It calculates birth charts accurately, explains them with classical rules, and works in English, Hindi and Marathi.

The repository is a monorepo so the web interface, API and calculation engine change together.

## What it does (first release)

- **Birth charts (Kundli):** sidereal zodiac with Lahiri ayanamsa (others selectable), whole-sign houses, North and South Indian styles, all 16 divisional charts (D1 to D60) and Sripati Bhava Chalit.
- **Planets:** sign, degree, Nakshatra and pada, dignity, retrograde and combust status.
- **Vimshottari Dasha:** Mahadasha, Antardasha and Pratyantardasha with exact dates.
- **Transits:** today's planets from Lagna and Moon, Sade Sati, Saturn and Jupiter sign changes.
- **Panchang:** sunrise, sunset, moonrise, moonset, Tithi, Nakshatra, Yoga, Karana and Vara for any day and place.
- **Readings:** 46 YAML rules (yogas and placements), each with its classical source, in three languages.
- **Strength:** Shadbala and Ashtakavarga (BAV and SAV).
- **Matching:** Ashtakoota (36 points) and Manglik check.
- **Accounts:** sign in with Google or an emailed link, explicit consent, saved charts in folders, CSV export, PDF reports, email alerts, data export and account deletion.
- **Public API:** API keys with daily and per-minute limits (`/api/public/v1/...`).
- **Admin:** user lookup; opening birth details needs a written reason and is logged.

AI explanations are not part of the first release.

## Accuracy

Accuracy is tested, not assumed. `packages/engine/tests/test_golden.py` checks 20 reference charts (1800 to 2399, both hemispheres, DST edge cases) against an independent calculation using NASA JPL DE421 through Skyfield (`tools/golden/make_reference.py`):

| Quantity | Tolerance in tests | Measured agreement |
|---|---|---|
| Planet longitudes | 1″ | ≤ 0.006″ |
| Mean nodes | 1″ | 0.09″ |
| Lagna | 1″ | 0.001″ |
| Dasha dates | 1 day | exact |

Lahiri ayanamsa matches the official value (23°15′00.658″ on 21 March 1956) within 1″, and Tithi changes match JPL new and full moons within one minute. CI runs these tests on every pull request.

## Project structure

```text
jyotish-app/
├── apps/
│   ├── api/             # FastAPI backend, Celery worker, migrations, PDF templates
│   └── web/             # Next.js frontend (en/hi/mr), unit and browser tests
├── packages/
│   └── engine/          # Python calculation engine (Swiss Ephemeris) and rule files
├── tools/golden/        # Builds the independent reference data for accuracy tests
├── docs/adr/            # Architecture Decision Records
├── infra/               # Deployment notes
├── .github/workflows/   # CI
├── docker-compose.yml   # Local development services
├── pyproject.toml       # Python workspace, Ruff, mypy, pytest settings
└── .env.example         # Example local configuration
```

## Run it locally (Docker)

You need Docker Desktop.

```bash
cp .env.example .env
docker compose up --build
```

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs
- Sign-in emails: http://localhost:8025 (Mailpit)

Sign in with any email address, then open the link from Mailpit. The first API start loads about 147,000 places for the city search, which takes a few seconds.

## Run it without Docker

You need Python 3.13 with [uv](https://docs.astral.sh/uv/), Node 22 with pnpm 10, PostgreSQL 16 or newer and Redis.

```bash
# Python: engine and API
uv sync --all-packages
cd apps/api
uv run alembic upgrade head
TASKS_EAGER=true uv run uvicorn jyotish_api.main:app --reload --port 8000

# Web (in another terminal)
cd apps/web
pnpm install
API_URL=http://localhost:8000 pnpm dev
```

Without an SMTP server the API prints sign-in links to its log.

## Tests and checks

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy apps/api/src packages/engine/src
uv run pytest                      # engine and API (needs Postgres and Redis)

cd apps/web
pnpm lint && pnpm typecheck && pnpm test && pnpm build
pnpm e2e                           # browser tests; needs the API and web app running
```

API tests use the database `jyotish_test` (`TEST_DATABASE_URL`) and Redis database 15.

## Configuration

See `.env.example`. In production the API refuses to start with the development `SECRET_KEY` or `DATA_ENCRYPTION_KEYS`. Google sign-in is shown only when `GOOGLE_CLIENT_ID` is set.

## Still needs expert review before launch

- Interpretation rules and texts (`packages/engine/src/jyotish_engine/rules/`) by a Jyotish expert.
- Matching tables (Yoni, Gana, Vashya) in `matching.py`, which follow common North Indian practice.
- Shadbala values compared with Jagannatha Hora for a sample of charts.
- Privacy policy and terms by a lawyer (the pages are marked as drafts).

## Licence

GNU Affero General Public License v3.0 (see `LICENSE`). The app uses the Swiss Ephemeris, which is free for AGPL projects. If you run a modified version as a service, you must offer its source code to users; the footer links to it.
