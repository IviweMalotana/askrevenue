// Display helpers for numbers and values.

const compact = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

const full = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

export function formatNumber(value: unknown): string {
  if (typeof value === "number") return full.format(value);
  return String(value ?? "");
}

export function formatCompact(value: unknown): string {
  if (typeof value === "number") return compact.format(value);
  return String(value ?? "");
}

export function isNumeric(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** Heuristic: does a measure name read like money? Used only for axis prefixing. */
export function looksMonetary(name: string): boolean {
  return /mrr|revenue|amount|arr|price|lost|cash|billing/i.test(name);
}

export function titleCase(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
