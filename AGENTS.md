# AGENTS.md

## Project direction

`main` is the development branch for the new local-first web application. The former Python/PySide6 desktop release is preserved in `legacy/desktop-v0.5.0`.

## Non-negotiable constraints

1. Never transmit patient, diagnosis, treatment, invoice, payment or practice data to a server.
2. Do not add analytics, session replay, advertising, remote logging or third-party error reporting.
3. All domain calculations, SQLite access, PDF generation, backup creation and encryption run locally.
4. Do not use floating-point numbers for money. Store integer cents.
5. Finalized invoices are immutable snapshots. Later master-data changes must not alter them.
6. Multi-record business operations must use SQLite transactions.
7. Medical data may be stored and displayed, but the product must not derive diagnoses, rank treatments or issue medical recommendations.
8. Any schema change requires a migration and tests.
9. Any import operation must be atomic, validated and non-destructive to the source files.
10. Never commit real patient data, invoices, practice configurations, databases, backups or identifying logos.

## Intended stack

- TypeScript with strict mode
- Vite
- a small component-oriented frontend framework selected by ADR
- PWA manifest and service worker
- SQLite compiled to WebAssembly
- SQLite work in a Web Worker
- File System Access API for an explicitly selected practice directory
- local PDF generation
- local encrypted ZIP-compatible or custom backup container
- Vitest for unit tests
- Playwright for browser integration tests

## Target structure

```text
web/
  src/
    domain/
    application/
    database/
    filesystem/
    documents/
    security/
    ui/
  public/
  tests/
docs/
```

Keep domain rules independent of UI and browser APIs. Browser-specific code belongs behind interfaces in `filesystem`, `database`, `documents` or `security`.

## Required quality gates

Before merging:

- formatting and linting pass
- TypeScript compilation passes without suppressions
- unit tests pass
- browser integration tests pass for current Chrome and Edge
- no network request contains domain data
- migration tests cover existing JSON fixtures
- invoice totals and payment balances use integer arithmetic
- finalized invoice snapshots remain stable

## First implementation milestone

Create a minimal installable PWA that:

1. opens without a backend,
2. can be installed,
3. remains usable offline,
4. selects and remembers a local practice directory where supported,
5. creates or opens a local SQLite database,
6. stores a test patient locally,
7. proves through an integration test that no patient data is sent over the network.
