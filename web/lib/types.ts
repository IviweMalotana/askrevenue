// Types mirroring the FastAPI response models.

export type ChartType = "line" | "bar" | "pie" | "area";

export interface ChartConfig {
  x: string | null;
  y: string[];
  series?: string | null;
}

export interface QueryResult {
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  truncated: boolean;
  row_limit: number;
  duration_ms: number;
  tables: string[];
}

export interface AnswerResponse {
  question: string;
  title: string;
  summary: string | null;
  chart_type: ChartType;
  chart_config: ChartConfig;
  result: QueryResult;
  source: "llm" | "fallback";
  matched: boolean;
}

export interface ExampleChip {
  title: string;
  question: string;
}

export interface SavedQuestion {
  id: number;
  title: string;
  question_text: string;
  generated_sql: string;
  chart_type: ChartType;
  chart_config: ChartConfig;
  summary: string | null;
  is_pinned: boolean;
}

export interface DashboardItem {
  saved_question: SavedQuestion;
  result: QueryResult | null;
  error: string | null;
}

export interface Dashboard {
  name: string;
  description: string | null;
  items: DashboardItem[];
}

export interface SchemaColumn {
  name: string;
  type: string;
  description: string;
  enum: string[] | null;
}

export interface SchemaTable {
  name: string;
  kind: "dimension" | "fact";
  description: string;
  columns: SchemaColumn[];
}

export interface HealthInfo {
  status: string;
  environment: string;
  llm_enabled: boolean;
}
