"use client";

import { useEffect, useState } from "react";
import { TableIcon } from "@/components/icons";
import { Badge, ErrorState, Skeleton, cn } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import type { SchemaTable } from "@/lib/types";

export default function SchemaPage() {
  const [tables, setTables] = useState<SchemaTable[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .schema()
      .then(setTables)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Could not load the schema."),
      );
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8 md:py-10">
      <header className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Schema</h1>
        <p className="mt-1 max-w-prose text-muted">
          Exactly what the AI is allowed to query — a clean star schema. Every
          generated query is validated against this allow-list before it runs, and
          nothing outside these tables is reachable.
        </p>
      </header>

      {error && (
        <div className="card">
          <ErrorState message={error} />
        </div>
      )}

      {!tables && !error && (
        <div className="space-y-5">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full" />
          ))}
        </div>
      )}

      {tables && (
        <div className="space-y-5">
          {tables.map((t) => (
            <TableCard key={t.name} table={t} />
          ))}
        </div>
      )}
    </div>
  );
}

function TableCard({ table }: { table: SchemaTable }) {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-border bg-surface-2 px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-md",
              table.kind === "fact"
                ? "bg-accent-soft text-accent"
                : "bg-teal-50 text-positive",
            )}
          >
            <TableIcon width={16} height={16} />
          </span>
          <div>
            <h3 className="font-mono text-base font-semibold text-ink">{table.name}</h3>
            <p className="text-xs text-muted">{table.description}</p>
          </div>
        </div>
        <Badge tone={table.kind === "fact" ? "accent" : "positive"}>{table.kind}</Badge>
      </div>

      <div className="scroll-thin overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left">
              <th className="border-b border-border px-4 py-2 font-medium text-muted">Column</th>
              <th className="border-b border-border px-4 py-2 font-medium text-muted">Type</th>
              <th className="border-b border-border px-4 py-2 font-medium text-muted">Description</th>
            </tr>
          </thead>
          <tbody>
            {table.columns.map((c) => (
              <tr key={c.name} className="align-top">
                <td className="whitespace-nowrap border-b border-border px-4 py-2 font-mono text-ink">
                  {c.name}
                </td>
                <td className="whitespace-nowrap border-b border-border px-4 py-2 font-mono text-xs text-muted">
                  {c.type}
                </td>
                <td className="border-b border-border px-4 py-2 text-muted">
                  {c.description}
                  {c.enum && (
                    <span className="mt-1 flex flex-wrap gap-1">
                      {c.enum.map((v) => (
                        <span
                          key={v}
                          className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-2xs text-faint"
                        >
                          {v}
                        </span>
                      ))}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
