import { formatNumber, isNumeric, titleCase } from "@/lib/format";

interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  max?: number;
}

export default function DataTable({ columns, rows, max = 100 }: Props) {
  const shown = rows.slice(0, max);
  return (
    <div className="scroll-thin overflow-auto rounded-md border border-border">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-surface-2 text-left">
            {columns.map((c) => (
              <th
                key={c}
                className="whitespace-nowrap border-b border-border px-3 py-2 font-medium text-muted"
              >
                {titleCase(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, i) => (
            <tr key={i} className="even:bg-surface-2/40">
              {columns.map((c) => (
                <td
                  key={c}
                  className={
                    "whitespace-nowrap border-b border-border px-3 py-1.5 " +
                    (isNumeric(row[c]) ? "text-right tabular-nums text-ink" : "text-muted")
                  }
                >
                  {isNumeric(row[c]) ? formatNumber(row[c]) : String(row[c] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > max && (
        <div className="border-t border-border px-3 py-2 text-xs text-faint">
          Showing first {max} of {rows.length} rows.
        </div>
      )}
    </div>
  );
}
