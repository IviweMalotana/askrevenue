"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartConfig, ChartType } from "@/lib/types";
import { formatCompact, formatNumber, looksMonetary, titleCase } from "@/lib/format";

// Restrained categorical palette anchored on the accent.
const PALETTE = [
  "#4F46E5",
  "#0F766E",
  "#B45309",
  "#9333EA",
  "#2563EB",
  "#DB2777",
  "#65A30D",
];

const AXIS = "#A8A29E";
const GRID = "#EFEDEB";

interface Props {
  chartType: ChartType;
  config: ChartConfig;
  columns: string[];
  rows: Record<string, unknown>[];
  height?: number;
}

function axisFormatter(monetary: boolean) {
  return (v: unknown) => (monetary ? `$${formatCompact(v)}` : formatCompact(v));
}

function tooltipFormatter(monetary: boolean) {
  return (v: unknown) => (monetary ? `$${formatNumber(v)}` : formatNumber(v));
}

const tooltipStyle = {
  borderRadius: 8,
  border: "1px solid #E7E5E4",
  boxShadow: "0 4px 16px -2px rgba(28,25,23,0.10)",
  fontSize: 12,
  padding: "8px 10px",
};

export default function ChartView({
  chartType,
  config,
  columns,
  rows,
  height = 320,
}: Props) {
  const x = config.x ?? columns[0];
  const ys = config.y.length ? config.y : columns.slice(1);
  const monetary = ys.some(looksMonetary);

  const common = {
    margin: { top: 8, right: 16, bottom: 4, left: 4 },
  };

  if (chartType === "pie") {
    const valueKey = ys[0] ?? columns[1];
    const data = rows.map((r) => ({
      name: String(r[x] ?? ""),
      value: typeof r[valueKey] === "number" ? (r[valueKey] as number) : 0,
    }));
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="52%"
            outerRadius="80%"
            paddingAngle={1.5}
            stroke="#fff"
            strokeWidth={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip formatter={tooltipFormatter(monetary)} contentStyle={tooltipStyle} />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: 12, color: "#57534E" }}
          />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={rows} {...common}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey={x} tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={{ stroke: GRID }} />
          <YAxis tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={false} tickFormatter={axisFormatter(monetary)} width={52} />
          <Tooltip formatter={tooltipFormatter(monetary)} contentStyle={tooltipStyle} />
          {ys.length > 1 && <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: "#57534E" }} />}
          {ys.map((y, i) => (
            <Line
              key={y}
              type="monotone"
              dataKey={y}
              name={titleCase(y)}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "area") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={rows} {...common}>
          <defs>
            {ys.map((y, i) => (
              <linearGradient key={y} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0.25} />
                <stop offset="100%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0.02} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey={x} tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={{ stroke: GRID }} />
          <YAxis tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={false} tickFormatter={axisFormatter(monetary)} width={52} />
          <Tooltip formatter={tooltipFormatter(monetary)} contentStyle={tooltipStyle} />
          {ys.map((y, i) => (
            <Area
              key={y}
              type="monotone"
              dataKey={y}
              name={titleCase(y)}
              stroke={PALETTE[i % PALETTE.length]}
              strokeWidth={2}
              fill={`url(#grad-${i})`}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  // bar (default)
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} {...common}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey={x} tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={{ stroke: GRID }} />
        <YAxis tick={{ fontSize: 11, fill: AXIS }} tickLine={false} axisLine={false} tickFormatter={axisFormatter(monetary)} width={52} />
        <Tooltip formatter={tooltipFormatter(monetary)} cursor={{ fill: "#F5F5F4" }} contentStyle={tooltipStyle} />
        {ys.length > 1 && <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: "#57534E" }} />}
        {ys.map((y, i) => (
          <Bar key={y} dataKey={y} name={titleCase(y)} fill={PALETTE[i % PALETTE.length]} radius={[3, 3, 0, 0]} maxBarSize={48} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
