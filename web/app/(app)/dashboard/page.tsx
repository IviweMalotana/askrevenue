"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import ChartCard from "@/components/ChartCard";
import SqlBlock from "@/components/SqlBlock";
import { ChevronIcon, GridIcon, RefreshIcon, SparkIcon, TrashIcon } from "@/components/icons";
import { Button, EmptyState, ErrorState, Skeleton, cn } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import type { Dashboard, DashboardItem, QueryResult } from "@/lib/types";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDashboard(await api.dashboard());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load the dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function removeItem(id: number) {
    setDashboard((d) =>
      d
        ? { ...d, items: d.items.filter((it) => it.saved_question.id !== id) }
        : d,
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-10">
      <header className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink">
            {dashboard?.name ?? "Dashboard"}
          </h1>
          <p className="mt-1 text-muted">
            {dashboard?.description ??
              "Saved and pinned questions, re-run live against current data."}
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={load} disabled={loading}>
          <RefreshIcon width={14} height={14} /> Refresh
        </Button>
      </header>

      {loading && <DashboardSkeleton />}

      {!loading && error && (
        <div className="card">
          <ErrorState
            message={error}
            action={<Button onClick={load}>Try again</Button>}
          />
        </div>
      )}

      {!loading && !error && dashboard && dashboard.items.length === 0 && (
        <div className="card">
          <EmptyState
            icon={<GridIcon width={28} height={28} />}
            title="No pinned charts yet"
            description="Ask a question and save it to build your dashboard."
            action={
              <Link href="/ask">
                <Button variant="primary">
                  <SparkIcon width={16} height={16} /> Ask a question
                </Button>
              </Link>
            }
          />
        </div>
      )}

      {!loading && !error && dashboard && dashboard.items.length > 0 && (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {dashboard.items.map((item) => (
            <DashboardCard
              key={item.saved_question.id}
              item={item}
              onRemoved={removeItem}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DashboardCard({
  item,
  onRemoved,
}: {
  item: DashboardItem;
  onRemoved: (id: number) => void;
}) {
  const sq = item.saved_question;
  const [result, setResult] = useState<QueryResult | null>(item.result);
  const [error, setError] = useState<string | null>(item.error);
  const [busy, setBusy] = useState(false);
  const [showSql, setShowSql] = useState(false);

  async function refresh() {
    setBusy(true);
    try {
      setResult(await api.runSaved(sq.id));
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Re-run failed.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    try {
      await api.setPin(sq.id, false);
      onRemoved(sq.id);
    } catch {
      setBusy(false);
    }
  }

  const actions = (
    <div className="flex items-center gap-0.5">
      <IconBtn label="Re-run" onClick={refresh} disabled={busy}>
        <RefreshIcon width={15} height={15} className={busy ? "animate-spin" : ""} />
      </IconBtn>
      <IconBtn label="Show SQL" onClick={() => setShowSql((v) => !v)}>
        <ChevronIcon
          width={15}
          height={15}
          className={cn("transition-transform", !showSql && "-rotate-90")}
        />
      </IconBtn>
      <IconBtn label="Remove from dashboard" onClick={remove} disabled={busy} danger>
        <TrashIcon width={15} height={15} />
      </IconBtn>
    </div>
  );

  return (
    <div className="space-y-2">
      {result ? (
        <ChartCard
          title={sq.title}
          chartType={sq.chart_type}
          config={sq.chart_config}
          result={result}
          actions={actions}
          height={260}
        />
      ) : (
        <div className="card">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h3 className="truncate text-base font-semibold text-ink">{sq.title}</h3>
            {actions}
          </div>
          <ErrorState
            title="Query failed"
            message={error ?? "This saved query could not be run."}
            action={<Button size="sm" onClick={refresh}>Retry</Button>}
          />
        </div>
      )}
      {showSql && <SqlBlock sql={sq.generated_sql} defaultOpen tables={result?.tables} />}
    </div>
  );
}

function IconBtn({
  label,
  onClick,
  disabled,
  danger,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex h-7 w-7 items-center justify-center rounded-md text-faint transition-colors hover:bg-surface-2 hover:text-ink disabled:opacity-40",
        danger && "hover:text-negative",
      )}
    >
      {children}
    </button>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-6 w-20" />
          </div>
          <div className="px-4 py-4">
            <Skeleton className="h-[240px] w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
