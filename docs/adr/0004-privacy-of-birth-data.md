# ADR 0004: Protecting birth data

- **Status:** Accepted
- **Date:** 2026-10-28

## Decision

- Birth details (date, time, place, coordinates) are encrypted at rest with Fernet (`DATA_ENCRYPTION_KEYS`, several keys allowed for rotation).
- Users must give recorded consent (purpose `chart_calculation`, version `2026-10`) before any chart is stored.
- Staff can open birth details only through the admin screen with a written reason of at least 10 characters; each access goes to the audit log.
- Users can export all their data as JSON and delete their account, which removes charts, reports and sessions and anonymises audit entries.
- PDF reports are deleted after 30 days. Error reports (Sentry, optional) strip request bodies and cookies.
- Hosting region is India (Mumbai), in line with the DPDP Act.
