export type Company = {
  id: number;
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
};

export type NarrativeEvidence = {
  claim_id: number;
  speaker: string | null;
  speaker_block_id: number | null;
  claim_text: string;
  source_text: string | null;
  polarity: string | null;
  strength: string | null;
};

export type EventDiffItem = {
  cluster_id: number;
  cluster_key: string;
  topic: string | null;
  label: string | null;
  canonical_claim_text: string | null;
  drift_type: string;
  shift_type: string | null;
  evidence: NarrativeEvidence[];
};

export type EventDiffResponse = {
  ticker: string;
  company_name: string;
  comparison_family: string | null;
  latest_document_id: number | null;
  previous_document_id: number | null;
  event_diff: {
    new: EventDiffItem[];
    dropped: EventDiffItem[];
    strengthened: EventDiffItem[];
    weakened: EventDiffItem[];
    contradicted: EventDiffItem[];
    repeated: EventDiffItem[];
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function getCompanies(): Promise<Company[]> {
  return fetchJson<Company[]>("/companies/");
}

export async function getEventDiff(
  ticker: string,
  family = "earnings_call",
): Promise<EventDiffResponse> {
  return fetchJson<EventDiffResponse>(
    `/event-diff/${ticker.toUpperCase()}?family=${encodeURIComponent(family)}`,
  );
}

// ── Intelligence / Wedge-core v1 types ───────────────────────────────────────

export type StateShift = {
  from_sentiment: number | null;
  to_sentiment: number | null;
  delta: number | null;
  from_summary: string | null;
  to_summary: string | null;
};

export type EvidenceItem = {
  claim_id: number;
  verbatim: string | null;
  summary: string | null;
  polarity: string | null;
  confidence: number | null;
  speaker: string | null;
  section: string | null;
};

export type MarketSignal = {
  reacted_at: string | null;
  price_move_pct: number | null;
  volume_vs_avg: number | null;
  sentiment_score: number | null;
  options_iv_spike: boolean | null;
  call_put_ratio: number | null;
};

export type NarrativeChange = {
  transition_id: string;
  thread_id: string;
  thread_name: string;
  mechanism: string | null;
  speed: string | null;
  confidence: number;
  summary: string;
  time_period: string;
  occurred_at: string;
  state_shift: StateShift;
  evidence: EvidenceItem[];
  market_signal: MarketSignal | null;
};

export type NarrativeBrief = {
  company: {
    id: number;
    ticker: string;
    name: string;
    sector: string | null;
  };
  generated_at: string;
  window_start: string;
  window_end: string;
  narrative_changes: NarrativeChange[];
  counts: {
    total_transitions: number;
    with_evidence: number;
    with_market_signal: number;
    threads_active: number;
  };
};

export type ThreadState = {
  id: string;
  sentiment_score: number;
  summary: string;
  time_period: string;
  document_id: number | null;
  created_at: string | null;
};

export type NarrativeThreadDetail = {
  id: string;
  name: string;
  status: string | null;
  kpi_label: string | null;
  latest_state: {
    sentiment_score: number;
    summary: string;
    time_period: string;
  } | null;
};

export type ThreadsResponse = {
  threads: NarrativeThreadDetail[];
};

export type ThreadStatesResponse = {
  states: ThreadState[];
};

export async function getNarrativeBrief(
  ticker: string,
  params?: { since?: string; limit?: number; min_confidence?: number },
): Promise<NarrativeBrief> {
  const qs = new URLSearchParams();
  if (params?.since) qs.set("since", params.since);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.min_confidence != null) qs.set("min_confidence", String(params.min_confidence));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return fetchJson<NarrativeBrief>(
    `/api/v1/companies/${ticker.toUpperCase()}/narrative-brief/${query}`,
  );
}

export async function getThreads(ticker: string): Promise<ThreadsResponse> {
  return fetchJson<ThreadsResponse>(
    `/api/v1/companies/${ticker.toUpperCase()}/threads/`,
  );
}

export async function getThreadStates(
  ticker: string,
  threadId: string,
): Promise<ThreadStatesResponse> {
  return fetchJson<ThreadStatesResponse>(
    `/api/v1/companies/${ticker.toUpperCase()}/threads/${threadId}/states`,
  );
}
