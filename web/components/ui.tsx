import type { ButtonHTMLAttributes, ReactNode } from "react";
import { WarnIcon } from "./icons";

export function cn(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

// --- Button ----------------------------------------------------------------

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent-hover border border-transparent",
  secondary:
    "bg-surface text-ink border border-border-strong hover:bg-surface-2",
  ghost: "bg-transparent text-muted hover:text-ink hover:bg-surface-2 border border-transparent",
  danger:
    "bg-surface text-negative border border-border hover:border-negative/40 hover:bg-red-50",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-2.5 text-sm gap-1.5",
  md: "h-10 px-4 text-base gap-2",
};

export function Button({
  variant = "secondary",
  size = "md",
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
}) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

// --- Card ------------------------------------------------------------------

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn("card", className)}>{children}</div>;
}

// --- Badge -----------------------------------------------------------------

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "accent" | "positive" | "warning";
  children: ReactNode;
}) {
  const tones = {
    neutral: "bg-surface-2 text-muted border-border",
    accent: "bg-accent-soft text-accent-ink border-accent/20",
    positive: "bg-teal-50 text-positive border-teal-200",
    warning: "bg-amber-50 text-warning border-amber-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-2xs font-medium",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}

// --- Skeleton --------------------------------------------------------------

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} />;
}

// --- States ----------------------------------------------------------------

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      {icon && <div className="text-faint">{icon}</div>}
      <div className="space-y-1">
        <p className="text-lg font-medium text-ink">{title}</p>
        {description && (
          <p className="mx-auto max-w-prose text-sm text-muted">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  action,
}: {
  title?: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-50 text-negative">
        <WarnIcon width={20} height={20} />
      </div>
      <div className="space-y-1">
        <p className="text-base font-medium text-ink">{title}</p>
        <p className="mx-auto max-w-prose text-sm text-muted">{message}</p>
      </div>
      {action}
    </div>
  );
}
