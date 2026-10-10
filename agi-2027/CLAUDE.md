# AGI 2027: notes for coding agents

@AGENTS.md

- Read [SPEC.md](SPEC.md) and [PLAN.md](PLAN.md) before changing anything. Build in the
  milestone order in PLAN.md; at the end of each milestone, stop, report what was built and how
  to test it, and update PLAN.md (status) and SPEC.md (change log) for anything that changed.
- Next.js 16.4 with Cache Components and Partial Prefetching. Request-time reads (`cookies()`,
  Supabase calls with the user session, `new Date()`) must sit inside `<Suspense>` or call
  `connection()` first. Never pass functions or icon components from Server to Client
  Components. Read `node_modules/next/dist/docs/` before using an API you haven't checked.
- Format dates only with `src/lib/time.ts`: Node and browsers punctuate Intl output
  differently, which breaks hydration.
- Money: exact decimal strings plus a currency, totals per currency (`src/lib/money.ts`).
- Statuses: labels and colors come from `src/lib/statuses.ts` only.
- Database: migrations only, RLS on every table, explicit grants, SECURITY DEFINER functions
  with `set search_path = ''` for multi-step changes. Add database tests in `tests/db` for every
  policy and function (`npm run test:db`).
- Styling: tokens in `src/app/globals.css`. Lime (`brand`) is for the single main action or
  highlight on a screen. Mobile first; 44px tap targets; inputs at 16px on phones.
- Before pushing: `npm run lint && npm run typecheck && npm test && npm run test:db && npm run build`.
