"use client";

import { useEffect, useState } from "react";
import ChartCard from "@/components/ChartCard";
import SqlBlock from "@/components/SqlBlock";
import { ApiError, api } from "@/lib/api";
import type { AnswerResponse, ExampleChip } from "@/lib/types";
import {
  ArrowRightIcon,
  BoltIcon,
  CheckIcon,
  PlusIcon,
  SparkIcon,
} from "@/components/icons";
import { Badge, Button, ErrorState, Skeleton } from "@/components/ui";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [examples, setExamples] = useState<ExampleChip[]>([]);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.examples().then(setExamples).catch(() => setExamples([]));
  }, []);

  async function ask(q: string) {
    const query = q.trim();
    if (!query || loading) return;
    setQuestion(query);
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await api.ask(query);
      setAnswer(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unexpected error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8 md:py-10">
      <header className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight text-ink">Ask</h1>
        <p className="mt-1 text-muted">
          Ask a question about the subscription business in plain English. You get
          the SQL, a chart, and a one-paragraph answer.
        </p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
        className="flex items-center gap-2 rounded-lg border border-border-strong bg-surface p-2 shadow-card focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/30"
      >
        <SparkIcon className="ml-2 shrink-0 text-faint" width={18} height={18} />
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What was MRR by month last year?"
          className="min-w-0 flex-1 bg-transparent px-1 py-1.5 text-lg text-ink placeholder:text-faint focus:outline-none"
          autoFocus
        />
        <Button type="submit" variant="primary" disabled={loading || !question.trim()}>
          {loading ? "Thinking…" : "Ask"}
          {!loading && <ArrowRightIcon width={16} height={16} />}
        </Button>
      </form>

      <ExampleChips examples={examples} onPick={ask} />

      <div className="mt-8">
        {loading && <AnswerSkeleton question={question} />}
        {!loading && error && (
          <div className="card">
            <ErrorState message={error} />
          </div>
        )}
        {!loading && !error && answer && <AnswerView answer={answer} />}
        {!loading && !error && !answer && <IdleHint />}
      </div>
    </div>
  );
}

function ExampleChips({
  examples,
  onPick,
}: {
  examples: ExampleChip[];
  onPick: (q: string) => void;
}) {
  if (examples.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <span className="label mr-1">Try</span>
      {examples.slice(0, 6).map((ex) => (
        <button key={ex.title} className="chip" onClick={() => onPick(ex.question)}>
          {ex.title}
        </button>
      ))}
    </div>
  );
}

function IdleHint() {
  return (
    <div className="card border-dashed">
      <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-accent-soft text-accent">
          <SparkIcon width={22} height={22} />
        </div>
        <p className="text-lg font-medium text-ink">Ask your first question</p>
        <p className="max-w-prose text-sm text-muted">
          Try one of the examples above, or ask anything about customers,
          subscriptions, MRR, churn, or payments. The generated SQL is always shown
          so you can trust the answer.
        </p>
      </div>
    </div>
  );
}

function AnswerView({ answer }: { answer: AnswerResponse }) {
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState<number | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function save() {
    if (saving || savedId) return;
    setSaving(true);
    setSaveError(null);
    try {
      const sq = await api.saveQuestion({
        title: answer.title,
        question_text: answer.question,
        generated_sql: answer.result.sql,
        chart_type: answer.chart_type,
        chart_config: answer.chart_config,
        summary: answer.summary,
      });
      setSavedId(sq.id);
    } catch (e) {
      setSaveError(e instanceof ApiError ? e.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold text-ink">{answer.title}</h2>
          {answer.source === "llm" ? (
            <Badge tone="accent">
              <BoltIcon width={11} height={11} /> AI-generated
            </Badge>
          ) : (
            <Badge tone="neutral">Curated</Badge>
          )}
        </div>
        {savedId ? (
          <Badge tone="positive">
            <CheckIcon width={12} height={12} /> Pinned to dashboard
          </Badge>
        ) : (
          <Button size="sm" onClick={save} disabled={saving}>
            <PlusIcon width={14} height={14} />
            {saving ? "Saving…" : "Save to dashboard"}
          </Button>
        )}
      </div>

      {saveError && <p className="text-sm text-negative">{saveError}</p>}

      {answer.summary && (
        <div className="rounded-md border border-accent/15 bg-accent-soft/60 px-4 py-3 text-base leading-relaxed text-ink">
          {answer.summary}
        </div>
      )}

      <ChartCard
        title={answer.title}
        chartType={answer.chart_type}
        config={answer.chart_config}
        result={answer.result}
      />

      <SqlBlock sql={answer.result.sql} tables={answer.result.tables} />
    </div>
  );
}

function AnswerSkeleton({ question }: { question: string }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Skeleton className="h-6 w-48" />
      </div>
      <Skeleton className="h-16 w-full" />
      <div className="card">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-7 w-24" />
        </div>
        <div className="px-4 py-4">
          <Skeleton className="h-[300px] w-full" />
        </div>
      </div>
      <Skeleton className="h-10 w-full" />
      <p className="text-center text-sm text-faint">
        Generating SQL and running it safely for “{question}”…
      </p>
    </div>
  );
}
