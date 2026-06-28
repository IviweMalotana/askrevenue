"use client";

import { useState, type ReactNode } from "react";
import type { ChartConfig, ChartType, QueryResult } from "@/lib/types";
import ChartView from "./ChartView";
import DataTable from "./DataTable";
import { EmptyState } from "./ui";
import { cn } from "./ui";

interface Props {
  title: string;
  chartType: ChartType;
  config: ChartConfig;
  result: QueryResult;
  actions?: ReactNode;
  height?: number;
  defaultView?: "chart" | "table";
}

export default function ChartCard({
  title,
  chartType,
  config,
  result,
  actions,
  height = 320,
  defaultView = "chart",
}: Props) {
  const [view, setView] = useState<"chart" | "table">(defaultView);
  const empty = result.row_count === 0;

  return (
    <div className="card flex flex-col">
      <div className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <h3 className="min-w-0 truncate text-base font-semibold text-ink" title={title}>
          {title}
        </h3>
        <div className="flex shrink-0 items-center gap-1.5">
          <div className="flex rounded-md border border-border p-0.5">
            {(["chart", "table"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={cn(
                  "rounded px-2 py-0.5 text-xs font-medium capitalize transition-colors",
                  view === v ? "bg-surface-2 text-ink" : "text-faint hover:text-muted",
                )}
              >
                {v}
              </button>
            ))}
          </div>
          {actions}
        </div>
      </div>

      <div className="flex-1 px-4 py-4">
        {empty ? (
          <EmptyState
            title="No rows returned"
            description="The query ran successfully but matched no data."
          />
        ) : view === "chart" ? (
          <ChartView
            chartType={chartType}
            config={config}
            columns={result.columns}
            rows={result.rows}
            height={height}
          />
        ) : (
          <DataTable columns={result.columns} rows={result.rows} />
        )}
      </div>

      <div className="flex items-center gap-3 border-t border-border px-4 py-2 text-2xs text-faint">
        <span>
          {result.row_count.toLocaleString()} row{result.row_count === 1 ? "" : "s"}
        </span>
        <span>·</span>
        <span>{result.duration_ms} ms</span>
        {result.truncated && (
          <>
            <span>·</span>
            <span className="text-warning">capped at {result.row_limit}</span>
          </>
        )}
      </div>
    </div>
  );
}
