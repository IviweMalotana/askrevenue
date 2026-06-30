import type { Config } from "tailwindcss";

/**
 * Design system: calm, dense, operator-grade analytics tool.
 * One accent (indigo), neutral warm-gray surfaces, subtle borders over shadows,
 * a real type scale. Inspired by the craft of Metabase — not its brand.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#FAFAF9", // app background
        surface: "#FFFFFF", // cards
        "surface-2": "#F5F5F4", // subtle fills (chips, table headers)
        border: "#E7E5E4",
        "border-strong": "#D6D3D1",
        ink: "#1C1917", // primary text
        muted: "#57534E", // secondary text
        faint: "#A8A29E", // tertiary / placeholders
        accent: "#4F46E5", // indigo-600 — the single accent
        "accent-hover": "#4338CA",
        "accent-soft": "#EEF2FF", // indigo-50 tint
        "accent-ink": "#3730A3",
        positive: "#0F766E", // teal-700
        negative: "#B91C1C", // red-700
        warning: "#B45309", // amber-700
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1.1rem" }],
        sm: ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.875rem", { lineHeight: "1.4rem" }],
        lg: ["1rem", { lineHeight: "1.55rem" }],
        xl: ["1.125rem", { lineHeight: "1.65rem" }],
        "2xl": ["1.375rem", { lineHeight: "1.8rem" }],
        "3xl": ["1.75rem", { lineHeight: "2.1rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.6rem" }],
        "5xl": ["3rem", { lineHeight: "1.1" }],
      },
      borderRadius: {
        sm: "0.25rem",
        DEFAULT: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(28,25,23,0.04), 0 1px 3px 0 rgba(28,25,23,0.03)",
        pop: "0 4px 16px -2px rgba(28,25,23,0.10), 0 2px 6px -2px rgba(28,25,23,0.06)",
      },
      maxWidth: {
        prose: "68ch",
      },
    },
  },
  plugins: [],
};

export default config;
