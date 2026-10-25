# Jyotish App

Jyotish App is a web application for Vedic astrology. The repository is organized as a monorepo so the web interface, API, and astrology calculation engine can evolve together.

## Project structure

```text
jyotish-app/
├── apps/
│   ├── api/             # FastAPI backend, API tests, and database migrations
│   └── web/             # Next.js frontend
├── packages/
│   └── engine/          # Python astrology calculation engine
├── docs/
│   └── adr/             # Architecture Decision Records
├── infra/               # Infrastructure-related configuration
├── docker-compose.yml   # Local development services
├── pyproject.toml       # Root Python workspace and development tools
├── uv.lock              # Locked Python dependencies
├── .env.example         # Example local environment configuration
└── README.md            # Project setup and usage guide