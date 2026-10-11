# AGI 2027

The web platform for AGI 2027, a creator marketing agency for AI startups: a public site that
sells the agency and recruits creators, a creator portal, and the agency admin.

- **What we're building:** [SPEC.md](SPEC.md)
- **How, and where we are:** [PLAN.md](PLAN.md)

## Stack

Next.js 16 (App Router, Cache Components) · TypeScript · Supabase (Postgres, Auth, Storage,
Realtime) · Tailwind CSS 4 · Radix-based components in the shadcn style · Motion · Vitest.

## Run it locally

```bash
cp .env.example .env.local   # then fill in the dev Supabase keys
npm install
npm run dev                  # http://localhost:3000
```

The app runs without Supabase keys; anything that needs the database says it isn't connected.

## Checks

```bash
npm run lint
npm run typecheck
npm test                      # unit tests
npm run test:db               # database tests, needs TEST_DATABASE_URL
npm run build
```

`npm run test:db` creates a throwaway database on the Postgres server in `TEST_DATABASE_URL`,
loads a small stand-in for Supabase's `auth` schema (`tests/db/supabase-shim.sql`) and every
migration, runs the tests as real `anon` and `authenticated` callers, then drops the database.
GitHub Actions runs all of the above on every push that touches this folder.

## Database changes

Every schema change is a SQL file in `supabase/migrations/`, named `YYYYMMDDHHMMSS_what.sql`.
Never change the schema by hand in the Supabase dashboard. On every push to a feature branch,
GitHub Actions applies new migrations and `supabase/seed.sql` to the dev project (repository
secret `DEV_DATABASE_URL`).

Rules for every migration are at the top of
[`supabase/migrations/20261010000000_foundation.sql`](supabase/migrations/20261010000000_foundation.sql).

## Where things live

| Path | What |
| --- | --- |
| `src/app/(marketing)` | Public site |
| `src/app/(auth)` | Sign in, sign up, password reset |
| `src/app/dashboard` | Creator portal |
| `src/app/admin` | Agency admin |
| `src/app/styleguide` | Design system page |
| `src/components/ui` | Base components (buttons, fields, dialogs, …) |
| `src/components/layout` | Site header and footer, app shell, navigation |
| `src/lib` | Statuses, money, time, navigation, Supabase clients |
| `supabase/` | Migrations, seed data, local Supabase config |
| `tests/` | Unit and database tests |
