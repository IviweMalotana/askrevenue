import Link from "next/link";
import {
  ArrowRightIcon,
  BoltIcon,
  BrowserIcon,
  CodeIcon,
  DatabaseIcon,
  GithubIcon,
  GridIcon,
  LockIcon,
  ServerIcon,
  ShieldIcon,
  SparkIcon,
  TableIcon,
} from "@/components/icons";
import type { ReactNode } from "react";

export const metadata = {
  title: "AskRevenue — a natural-language analytics case study",
  description:
    "Turning plain-English questions into safe SQL, charts, and answers over a subscription business. A case study in the BA + AI overlap.",
};

export default function Landing() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <TopBar />
      <Hero />
      <main className="mx-auto max-w-5xl space-y-24 px-5 pb-28 md:px-8">
        <Problem />
        <Approach />
        <Architecture />
        <Safety />
        <Outcome />
        <CaseClose />
      </main>
      <Footer />
    </div>
  );
}

/* ------------------------------------------------------------------ */

function TopBar() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-canvas/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3.5 md:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-white">
            <SparkIcon width={18} height={18} />
          </span>
          <span className="text-lg font-semibold tracking-tight">AskRevenue</span>
        </Link>
        <nav className="flex items-center gap-1.5">
          <Link
            href="/schema"
            className="hidden rounded-md px-3 py-2 text-base font-medium text-muted hover:bg-surface-2 hover:text-ink sm:block"
          >
            Schema
          </Link>
          <Link
            href="/dashboard"
            className="hidden rounded-md px-3 py-2 text-base font-medium text-muted hover:bg-surface-2 hover:text-ink sm:block"
          >
            Dashboard
          </Link>
          <Link
            href="/ask"
            className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-base font-medium text-white hover:bg-accent-hover"
          >
            Live demo <ArrowRightIcon width={16} height={16} />
          </Link>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="mx-auto max-w-5xl px-5 pb-16 pt-16 md:px-8 md:pb-20 md:pt-24">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/20 bg-accent-soft px-3 py-1 text-xs font-medium text-accent-ink">
        <BoltIcon width={12} height={12} /> Case study · BA × AI
      </span>
      <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-5xl">
        Ask a subscription business anything —{" "}
        <span className="text-accent">in plain English.</span>
      </h1>
      <p className="mt-5 max-w-prose text-lg text-muted">
        AskRevenue turns natural-language questions into safe, read-only SQL over a
        realistic subscriptions dataset, then returns the right chart and a
        plain-English summary. The generated SQL is always shown — because clients
        distrust black-box text-to-SQL, and trust is the product.
      </p>
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Link
          href="/ask"
          className="inline-flex items-center gap-2 rounded-md bg-accent px-5 py-3 text-base font-medium text-white shadow-card hover:bg-accent-hover"
        >
          Open the live demo <ArrowRightIcon width={16} height={16} />
        </Link>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-md border border-border-strong bg-surface px-5 py-3 text-base font-medium text-ink hover:bg-surface-2"
        >
          <GridIcon width={16} height={16} /> View the dashboard
        </Link>
        <span className="text-sm text-faint">No login · seeded demo data</span>
      </div>

      <div className="mt-12 grid gap-3 sm:grid-cols-3">
        <FeatureLine icon={<SparkIcon width={18} height={18} />} title="NL → SQL">
          Grounded in a known schema; never invents tables.
        </FeatureLine>
        <FeatureLine icon={<ShieldIcon width={18} height={18} />} title="Safe by design">
          Single SELECT, validated, run on a read-only role.
        </FeatureLine>
        <FeatureLine icon={<GridIcon width={18} height={18} />} title="Operator-ready">
          Charts, summaries, saved dashboards — finished UI.
        </FeatureLine>
      </div>
    </section>
  );
}

function FeatureLine({
  icon,
  title,
  children,
}: {
  icon: ReactNode;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="card p-4">
      <div className="mb-2 flex items-center gap-2 text-accent">{icon}</div>
      <p className="font-medium text-ink">{title}</p>
      <p className="mt-0.5 text-sm text-muted">{children}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */

function SectionHeading({ kicker, title }: { kicker: string; title: string }) {
  return (
    <div className="mb-7">
      <p className="label mb-2">{kicker}</p>
      <h2 className="text-3xl font-semibold tracking-tight">{title}</h2>
    </div>
  );
}

function Problem() {
  return (
    <section>
      <SectionHeading kicker="The problem" title="Revenue questions outpace the people who can answer them" />
      <div className="grid gap-6 md:grid-cols-2">
        <p className="text-lg leading-relaxed text-muted">
          In a subscription business, the questions never stop — what's MRR doing,
          which plan churns, why are payments failing this quarter. Each one is a
          ticket to a data team, a few days of turnaround, and a dashboard that
          answers last week's question, not today's.
        </p>
        <p className="text-lg leading-relaxed text-muted">
          Generic text-to-SQL tools promise to close that gap, but operators won't
          act on a number they can't trace. The hard part isn't generating SQL —
          it's generating SQL that is <strong className="text-ink">correct</strong>,{" "}
          <strong className="text-ink">safe</strong>, and{" "}
          <strong className="text-ink">transparent</strong> enough to trust.
        </p>
      </div>
    </section>
  );
}

function Approach() {
  const steps = [
    {
      n: "01",
      title: "Ground the model in a real schema",
      body: "A clean star schema (customers, plans, subscriptions, payments, churn) is the single source of truth — it drives the prompt, the safety allow-list, and the schema explorer, so they never drift.",
    },
    {
      n: "02",
      title: "Generate, then prove it's safe",
      body: "Kimi returns one SELECT plus a chart proposal. Every query is parsed and validated — single statement, no writes, allow-listed tables only — before it ever runs, with a one-shot repair loop if it fails.",
    },
    {
      n: "03",
      title: "Execute read-only, show the work",
      body: "Validated SQL runs on a least-privilege Postgres role with a row cap and timeout. The exact SQL is shown by default, the chart type is chosen from the data, and a summary explains it in plain English.",
    },
  ];
  return (
    <section>
      <SectionHeading kicker="My approach" title="Make the AI trustworthy, not just clever" />
      <div className="grid gap-5 md:grid-cols-3">
        {steps.map((s) => (
          <div key={s.n} className="card p-5">
            <span className="font-mono text-sm text-accent">{s.n}</span>
            <h3 className="mt-2 text-lg font-semibold">{s.title}</h3>
            <p className="mt-2 text-base leading-relaxed text-muted">{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */

function Architecture() {
  return (
    <section>
      <SectionHeading kicker="Architecture" title="A small system with a strict safety boundary" />
      <div className="card p-6 md:p-8">
        <div className="grid items-stretch gap-4 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
          <ArchNode
            icon={<BrowserIcon width={20} height={20} />}
            title="Web — Next.js 15"
            host="Vercel"
            lines={["App Router + TypeScript", "Tailwind + Recharts", "Ask · Dashboard · Schema"]}
          />
          <Connector />
          <ArchNode
            icon={<ServerIcon width={20} height={20} />}
            title="API — FastAPI"
            host="Railway"
            accent
            lines={["NL→SQL via Kimi", "SQL safety validator", "Read-only executor"]}
          />
          <Connector />
          <ArchNode
            icon={<DatabaseIcon width={20} height={20} />}
            title="Postgres"
            host="Railway"
            lines={["Star schema + app tables", "SQLAlchemy · Alembic", "askrevenue_ro role"]}
          />
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
          <div className="hidden md:block" />
          <div className="hidden md:block" />
          <div className="rounded-md border border-dashed border-accent/30 bg-accent-soft/50 p-3 text-center">
            <p className="flex items-center justify-center gap-1.5 text-sm font-medium text-accent-ink">
              <SparkIcon width={14} height={14} /> Kimi (Moonshot AI)
            </p>
            <p className="mt-0.5 text-xs text-muted">
              schema-grounded · structured output
            </p>
          </div>
          <div className="hidden md:block" />
          <div className="rounded-md border border-dashed border-positive/30 bg-teal-50/60 p-3 text-center">
            <p className="flex items-center justify-center gap-1.5 text-sm font-medium text-positive">
              <LockIcon width={14} height={14} /> SELECT-only role
            </p>
            <p className="mt-0.5 text-xs text-muted">no writes, ever</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function ArchNode({
  icon,
  title,
  host,
  lines,
  accent,
}: {
  icon: ReactNode;
  title: string;
  host: string;
  lines: string[];
  accent?: boolean;
}) {
  return (
    <div
      className={
        "rounded-lg border bg-surface p-4 " +
        (accent ? "border-accent/30 ring-1 ring-accent/10" : "border-border")
      }
    >
      <div className="flex items-center justify-between">
        <span className={accent ? "text-accent" : "text-muted"}>{icon}</span>
        <span className="rounded bg-surface-2 px-1.5 py-0.5 text-2xs font-medium text-faint">
          {host}
        </span>
      </div>
      <p className="mt-2 font-semibold text-ink">{title}</p>
      <ul className="mt-2 space-y-1">
        {lines.map((l) => (
          <li key={l} className="text-sm text-muted">
            {l}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Connector() {
  return (
    <div className="flex items-center justify-center text-faint">
      <ArrowRightIcon className="hidden md:block" width={20} height={20} />
      <ArrowRightIcon className="rotate-90 md:hidden" width={18} height={18} />
    </div>
  );
}

/* ------------------------------------------------------------------ */

function Safety() {
  const items = [
    { icon: <CodeIcon width={18} height={18} />, t: "One statement, SELECT only", d: "Parsed with an AST; DML/DDL, multiple statements, and comment tricks are rejected before execution." },
    { icon: <TableIcon width={18} height={18} />, t: "Allow-listed tables", d: "Only the analytics tables are reachable — app tables and system catalogs are blocked outright." },
    { icon: <LockIcon width={18} height={18} />, t: "Least-privilege role", d: "Validated SQL runs on a dedicated read-only Postgres role — defence in depth even if a check were bypassed." },
    { icon: <ShieldIcon width={18} height={18} />, t: "Bounded & transparent", d: "Row cap and statement timeout, and the exact SQL is shown to the user with every answer." },
  ];
  return (
    <section>
      <SectionHeading kicker="Why it's trustworthy" title="Four layers between a question and the database" />
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((i) => (
          <div key={i.t} className="card flex gap-3 p-5">
            <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent-soft text-accent">
              {i.icon}
            </span>
            <div>
              <p className="font-semibold text-ink">{i.t}</p>
              <p className="mt-0.5 text-base leading-relaxed text-muted">{i.d}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ */

function Outcome() {
  return (
    <section>
      <SectionHeading kicker="The outcome" title="Two layers — what's shipped, and what it delivers" />

      {/* What's verifiable today: real facts about the build itself. */}
      <div className="mb-10">
        <p className="label mb-3">Shipped today · verifiable on the demo</p>
        <div className="grid gap-4 sm:grid-cols-3">
          <Shipped value="100%" label="Read-only by construction" hint="No DML can execute — enforced by both the validator and the Postgres role." />
          <Shipped value="40" label="Automated safety tests" hint="Cover the unsafe-SQL matrix, row caps, statement timeouts, and JSON serialisation." />
          <Shipped value="5" label="Analytics tables in scope" hint="A clean star schema; system catalogs and app tables are blocked outright." />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <Shipped value="<50ms" label="Typical query latency" hint="On the seeded demo dataset, including JSON serialisation." />
          <Shipped value="24mo" label="Simulated history" hint="Coherent MRR growth, tier-dependent churn, realistic payment-failure mix." />
          <Shipped value="0" label="Secrets in source" hint="API keys are read from env vars; .env is gitignored." />
        </div>
      </div>

      {/* What needs a real engagement to fill in — explicit placeholders. */}
      <div>
        <p className="label mb-3">In production · awaiting real usage</p>
        <div className="mb-5 flex items-start gap-2 rounded-md border border-dashed border-warning/40 bg-amber-50/60 px-4 py-3 text-sm text-warning">
          <span className="font-medium">Placeholders —</span>
          <span className="text-muted">
            The business outcomes below are clearly marked for me to fill from a
            real engagement or production usage. They are intentionally not invented.
          </span>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Metric label="Time-to-answer, before → after" hint="e.g. 3 days → 30 seconds" />
          <Metric label="Analyst hours saved / month" hint="ad-hoc query load removed" />
          <Metric label="Questions self-served" hint="share answered without a data ticket" />
        </div>
      </div>
    </section>
  );
}

function Shipped({ value, label, hint }: { value: string; label: string; hint: string }) {
  return (
    <div className="card p-5">
      <span className="font-mono text-3xl font-semibold tracking-tight text-ink">
        {value}
      </span>
      <p className="mt-2 font-medium text-ink">{label}</p>
      <p className="mt-0.5 text-sm leading-relaxed text-muted">{hint}</p>
    </div>
  );
}

function Metric({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="rounded-lg border-2 border-dashed border-border-strong bg-surface p-5">
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-3xl font-semibold tracking-tight text-faint">
          00
        </span>
        <span className="rounded bg-surface-2 px-1.5 py-0.5 text-2xs font-medium uppercase tracking-wide text-faint">
          fill in
        </span>
      </div>
      <p className="mt-2 font-medium text-ink">{label}</p>
      <p className="mt-0.5 text-sm text-muted">{hint}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */

function CaseClose() {
  return (
    <section>
      <div className="card overflow-hidden">
        <div className="grid gap-0 md:grid-cols-[1.3fr_1fr]">
          <div className="p-7 md:p-9">
            <p className="label mb-2">Why I built this</p>
            <h2 className="text-2xl font-semibold tracking-tight">
              It sits exactly on the BA + AI overlap
            </h2>
            <p className="mt-3 text-base leading-relaxed text-muted">
              The years I've spent on the BA side of billing and analytics — across
              DynamoDB, BigQuery, Pandas, and a lot of Recharts — taught me where
              the friction actually is. It's rarely the data; it's the round-trip
              between a stakeholder's question and a trustworthy answer.
            </p>
            <p className="mt-3 text-base leading-relaxed text-muted">
              AskRevenue is the project where I get to apply what an AI can do to
              that exact gap, with the guardrails an analyst would actually
              require: <strong className="text-ink">read-only by construction</strong>,
              schema-grounded, and never hiding the query.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/ask"
                className="inline-flex items-center gap-2 rounded-md bg-accent px-5 py-3 text-base font-medium text-white hover:bg-accent-hover"
              >
                Try the live demo <ArrowRightIcon width={16} height={16} />
              </Link>
              <a
                href="https://github.com/IviweMalotana/askrevenue"
                className="inline-flex items-center gap-2 rounded-md border border-border-strong bg-surface px-5 py-3 text-base font-medium text-ink hover:bg-surface-2"
              >
                <GithubIcon width={16} height={16} /> Source code
              </a>
            </div>
          </div>
          <div className="border-t border-border bg-surface-2 p-7 md:border-l md:border-t-0 md:p-9">
            <p className="label mb-3">Stack</p>
            <ul className="space-y-2 text-sm text-muted">
              <li><span className="text-ink">Frontend</span> — Next.js 15, TypeScript, Tailwind, Recharts</li>
              <li><span className="text-ink">Backend</span> — FastAPI, Python 3.12, uv</li>
              <li><span className="text-ink">Data</span> — Postgres, SQLAlchemy, Alembic, sqlglot</li>
              <li><span className="text-ink">AI</span> — Kimi K2 (Moonshot, OpenAI-compatible)</li>
              <li><span className="text-ink">Deploy</span> — Vercel (web) · Railway (api + db)</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 px-5 py-8 text-sm text-faint md:flex-row md:px-8">
        <p>AskRevenue — a natural-language analytics case study.</p>
        <div className="flex gap-4">
          <Link href="/ask" className="hover:text-ink">Demo</Link>
          <Link href="/schema" className="hover:text-ink">Schema</Link>
          <a href="https://github.com/IviweMalotana/askrevenue" className="hover:text-ink">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
