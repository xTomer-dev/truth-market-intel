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
};

export type NarrativeCluster = {
  cluster_id: number;
  cluster_key: string;
  topic: string | null;
  label: string | null;
  canonical_claim_text: string | null;
  evidence: NarrativeEvidence[];
};

export type CompanySummary = {
  ticker: string;
  company_name: string;
  latest_document_id: number | null;
  summary: {
    new: NarrativeCluster[];
    repeated: NarrativeCluster[];
    dropped: NarrativeCluster[];
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

export async function getCompanySummary(ticker: string): Promise<CompanySummary> {
  return fetchJson<CompanySummary>(`/company-summary/${ticker.toUpperCase()}`);
}
