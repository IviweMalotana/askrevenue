# Deploying AskRevenue

Three pieces ship independently: **Postgres** and the **API** on Railway, and the
**web** app on Vercel. GitHub Actions wires up auto-deploy on push to `main`.

This runbook is the exact sequence to take a fresh fork to a live demo at
`https://askrevenue.victorthelabel.com`. Substitute your own domain anywhere
you see it.

> Rotate any API key the moment it leaves a private vault. Treat every key in
> this doc as a placeholder.

---

## 1. Railway — API + Postgres

1. Go to <https://railway.com> and log in.
2. Open the project called **`portfolio`** (or create one).
3. **Add Postgres.** Add Service → Database → PostgreSQL. pgvector is **not**
   required for AskRevenue.
4. Provision the read-only role once. Open the Postgres service → *Query* and
   paste the contents of [`infra/db-init/01-readonly-role.sql`](infra/db-init/01-readonly-role.sql).
5. **Add the API service.** New Service → "Deploy from GitHub repo" → select
   **`iviwemalotana/askrevenue`** → Root Directory **`api`**. Name it
   **`askrevenue-api`**.
6. On `askrevenue-api` → **Variables**, set:

   | Variable                | Value                                                                                                       |
   | ----------------------- | ----------------------------------------------------------------------------------------------------------- |
   | `DATABASE_URL`          | Reference the Postgres plugin's `DATABASE_URL`                                                              |
   | `READONLY_DATABASE_URL` | Same host/db as `DATABASE_URL` but with user `askrevenue_ro` and password `askrevenue_ro`                   |
   | `ANTHROPIC_API_KEY`     | Your Claude key. Leave blank to ship with the curated fallback only.                                        |
   | `ANTHROPIC_MODEL`       | `claude-haiku-4-5` (cheapest tier; bump to `claude-sonnet-4-6` for harder prompts)                          |
   | `CORS_ORIGINS`          | `https://askrevenue.victorthelabel.com` (add the Vercel preview URL too if you want previews to work)       |
   | `ENVIRONMENT`           | `production`                                                                                                |
   | `PORT`                  | `8000`                                                                                                      |

7. Settings → **Networking** → **Generate Domain**. Note the URL
   (e.g. `askrevenue-api.up.railway.app`). You'll need it for Vercel.
8. Trigger a deploy if it didn't start automatically. The `Procfile` runs
   `alembic upgrade head` on every release.
9. **Seed the demo data once** after the first successful deploy, from the
   Railway shell on `askrevenue-api`:

   ```bash
   uv run python -m app.seed
   psql "$DATABASE_URL" -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO askrevenue_ro;"
   ```

10. Smoke-test:

    ```bash
    curl https://<railway-domain>/health
    # {"status":"ok","environment":"production","llm_enabled":true}
    ```

## 2. Vercel — Frontend

1. Go to <https://vercel.com> and log in.
2. Add New Project → Import Git Repository → select **`iviwemalotana/askrevenue`**.
3. Root Directory **`web`**.
4. Environment Variables:

   | Variable                   | Value                                                                |
   | -------------------------- | -------------------------------------------------------------------- |
   | `NEXT_PUBLIC_API_BASE_URL` | `https://<the Railway domain from step 1.7>`                          |

5. **Deploy.**
6. After deploy succeeds: project → Settings → **Domains** → Add Domain →
   `askrevenue.victorthelabel.com` → follow the DNS instructions at your
   registrar.
7. Back in Railway → `askrevenue-api` → Variables → update `CORS_ORIGINS` so it
   includes the final Vercel domain.

## 3. GitHub Actions — auto-deploy on push to `main`

1. Get four tokens:

   | Secret              | Where                                                                       |
   | ------------------- | --------------------------------------------------------------------------- |
   | `RAILWAY_TOKEN`     | railway.com → Account Settings → Tokens → New Token                          |
   | `VERCEL_TOKEN`      | vercel.com → Settings → Tokens → Create                                      |
   | `VERCEL_ORG_ID`     | vercel.com → Settings → General → "Your ID"                                  |
   | `VERCEL_PROJECT_ID` | The Vercel project → Settings → General → "Project ID"                       |

2. Add them at
   <https://github.com/iviwemalotana/askrevenue/settings/secrets/actions>.
3. The workflow at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
   picks them up on the next push to `main`.

## 4. Merge the deploy branch

1. Open <https://github.com/iviwemalotana/askrevenue/pulls>.
2. Merge the PR for branch `claude/portfolio-product-setup-hb5vpm`. The merge
   to `main` triggers the first GitHub Actions deploy.

---

## Notes

- **Demo mode is safe to ship publicly.** No login, read-only queries only.
  Without an `ANTHROPIC_API_KEY` the Ask view falls back to a curated example
  library — the example chips always work; set a key to enable live NL→SQL.
- **The read-only role is the security boundary.** Keep
  `READONLY_DATABASE_URL` pointed at `askrevenue_ro`, never the owner role,
  in production. Re-grant SELECT after re-seeding (the seed creates new tables).
- **Provider URL shapes are handled.** `postgres://` or `postgresql://` URLs
  from Railway/Heroku are rewritten to `postgresql+psycopg://` automatically.
- **Cost.** Haiku 4.5 at $1/$5 per 1M tokens is plenty for short
  schema-grounded NL→SQL. A typical Ask costs well under $0.001.

## Diffs from the clause-rag deploy

If you're porting from the clause-rag blueprint:

| | clause-rag | askrevenue |
| --- | --- | --- |
| Repo | `iviwemalotana/clause-rag` | `iviwemalotana/askrevenue` |
| API service | `clause-api` | `askrevenue-api` |
| Domain | `clause.victorthelabel.com` | `askrevenue.victorthelabel.com` |
| AI keys | `ANTHROPIC_API_KEY` + `OPENAI_API_KEY` | `ANTHROPIC_API_KEY` only |
| Extra env | — | `ANTHROPIC_MODEL`, `READONLY_DATABASE_URL`, `ENVIRONMENT` |
| Postgres | pgvector required | stock Postgres |
| Post-deploy | — | `uv run python -m app.seed` + re-grant SELECT |
