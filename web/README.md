# AskRevenue Web

Next.js 15 (App Router) + TypeScript + Tailwind + Recharts frontend.

```bash
npm install
npm run dev      # http://localhost:3000  (expects the API on :8000)
```

Set `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`) to point at the
backend. See the [top-level README](../README.md) for the full architecture.

## Routes

- `/ask` — ask a question; see generated SQL, a chart, and a summary.
- `/dashboard` — saved/pinned charts, re-run live.
- `/schema` — browse the tables the AI may query.
- `/` — redirects to `/ask` (the case-study landing page lands in a later milestone).
