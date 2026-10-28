# ADR 0003: Self-hosted sign-in with Google and email links

- **Status:** Accepted (replaces the "managed OIDC (Clerk)" choice in the SDLC handbook)
- **Date:** 2026-10-28

## Context

The product owner chose sign-in with Google and email only (no phone OTP), and a free first release. A managed provider would add a monthly cost per active user and another processor of personal data.

## Decision

The API handles sign-in itself:

- **Email:** a one-time link (15 minutes) to `/auth/verify`. The page, not the link, sends the token to the API, so email scanners that open links cannot use it up. Tokens are stored only as keyed hashes.
- **Google:** OpenID Connect with `state` and `nonce`; the ID token is verified against Google's keys.
- **Sessions:** random token in an httpOnly, SameSite=Lax cookie (`Secure` over HTTPS), stored hashed, 30 days.
- **CSRF:** every state-changing request must carry `X-CSRF: 1`, which a cross-site form cannot send.
- Rate limits on sign-in requests per address and per IP.

## Consequences

- No third-party cost or data processor for sign-in.
- We own security fixes for this code. It is small and covered by API tests.
- Adding phone OTP later would need an SMS provider.
