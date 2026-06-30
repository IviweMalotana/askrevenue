"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import { BoltIcon, GridIcon, SparkIcon, TableIcon } from "./icons";
import { Badge, cn } from "./ui";

const NAV = [
  { href: "/ask", label: "Ask", Icon: SparkIcon },
  { href: "/dashboard", label: "Dashboard", Icon: GridIcon },
  { href: "/schema", label: "Schema", Icon: TableIcon },
];

function StatusBadge() {
  const [live, setLive] = useState<boolean | null>(null);
  useEffect(() => {
    api
      .health()
      .then((h) => setLive(h.llm_enabled))
      .catch(() => setLive(null));
  }, []);
  if (live === null) return null;
  return live ? (
    <Badge tone="accent">
      <BoltIcon width={11} height={11} /> Live AI
    </Badge>
  ) : (
    <Badge tone="neutral">Demo · curated</Badge>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-surface px-3 py-4 md:flex">
        <Link href="/" className="mb-6 flex items-center gap-2.5 px-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-white">
            <SparkIcon width={18} height={18} />
          </span>
          <span className="text-lg font-semibold tracking-tight text-ink">
            AskRevenue
          </span>
        </Link>

        <nav className="flex flex-col gap-0.5">
          {NAV.map(({ href, label, Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-base font-medium transition-colors",
                  active
                    ? "bg-accent-soft text-accent-ink"
                    : "text-muted hover:bg-surface-2 hover:text-ink",
                )}
              >
                <Icon width={18} height={18} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 px-2">
          <StatusBadge />
          <p className="text-2xs leading-relaxed text-faint">
            Natural-language analytics over a subscription business. Every query
            is read-only and shown in full.
          </p>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-surface/90 px-4 py-3 backdrop-blur md:hidden">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-white">
              <SparkIcon width={16} height={16} />
            </span>
            <span className="font-semibold text-ink">AskRevenue</span>
          </Link>
          <nav className="flex gap-1">
            {NAV.map(({ href, label }) => {
              const active = pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "rounded px-2.5 py-1.5 text-sm font-medium",
                    active ? "bg-accent-soft text-accent-ink" : "text-muted",
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </header>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
