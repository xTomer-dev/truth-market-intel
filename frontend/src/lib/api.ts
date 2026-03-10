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
