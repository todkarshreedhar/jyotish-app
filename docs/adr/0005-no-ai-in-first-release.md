# ADR 0005: No AI explanations in the first release

- **Status:** Accepted
- **Date:** 2026-10-28

## Decision

The first release shows only rule-based readings: YAML rules evaluated by the engine, each with its classical source and texts in English, Hindi and Marathi. AI explanations are left out to keep the free service at zero model cost.

## Consequences

The rule engine output is stable and testable. If AI explanations are added later, they must only explain rule output and never calculate positions.
