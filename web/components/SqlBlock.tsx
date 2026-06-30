"use client";

import { useState } from "react";
import { ChevronIcon, CheckIcon, LockIcon } from "./icons";
import { Badge, cn } from "./ui";

interface Props {
  sql: string;
  tables?: string[];
  defaultOpen?: boolean;
}

export default function SqlBlock({ sql, tables = [], defaultOpen = true }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface">
      <div className="flex items-center justify-between gap-2 border-b border-border bg-surface-2 px-3 py-2">
        <button
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-ink"
          aria-expanded={open}
        >
          <ChevronIcon
            className={cn("text-faint transition-transform", !open && "-rotate-90")}
            width={14}
            height={14}
          />
          Generated SQL
        </button>
        <div className="flex items-center gap-2">
          <Badge tone="positive">
            <LockIcon width={11} height={11} /> read-only
          </Badge>
          <button
            onClick={copy}
            className="rounded px-2 py-1 text-xs text-muted transition-colors hover:bg-surface hover:text-ink"
          >
            {copied ? (
              <span className="flex items-center gap-1 text-positive">
                <CheckIcon width={12} height={12} /> Copied
              </span>
            ) : (
              "Copy"
            )}
          </button>
        </div>
      </div>
      {open && (
        <div>
          <pre className="scroll-thin max-h-72 overflow-auto px-4 py-3 font-mono text-xs leading-relaxed text-ink">
            <code>{sql}</code>
          </pre>
          {tables.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 border-t border-border px-4 py-2">
              <span className="label">tables</span>
              {tables.map((t) => (
                <span
                  key={t}
                  className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-2xs text-muted"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
