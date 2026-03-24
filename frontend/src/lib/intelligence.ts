import type { NarrativeChange, StateShift } from "./api";

export function formatSentiment(score: number | null | undefined): string {
  if (score == null) return "—";
  return score >= 0 ? `+${score.toFixed(2)}` : score.toFixed(2);
}

export function sentimentColor(score: number | null | undefined): string {
  if (score == null) return "#6b7280";
  if (score >= 0.4) return "#10b981";
  if (score >= 0.1) return "#34d399";
  if (score >= -0.1) return "#9ca3af";
  if (score >= -0.4) return "#f59e0b";
  return "#ef4444";
}

export function deltaColor(delta: number | null | undefined): string {
  if (delta == null) return "#6b7280";
  if (delta > 0.15) return "#10b981";
  if (delta > 0) return "#34d399";
  if (delta === 0) return "#9ca3af";
  if (delta > -0.15) return "#f59e0b";
  return "#ef4444";
}

export function mechanismLabel(mechanism: string | null | undefined): string {
  const map: Record<string, string> = {
    technical_milestone: "TECH MILESTONE",
    commercial_agreement: "COMMERCIAL AGR",
    capital_event: "CAPITAL EVENT",
    regulatory_change: "REGULATORY",
    product_launch: "PRODUCT LAUNCH",
    macro_shift: "MACRO SHIFT",
    management_guidance: "MGMT GUIDANCE",
    earnings_surprise: "EARNINGS",
    other: "OTHER",
  };
  return mechanism ? (map[mechanism] ?? mechanism.toUpperCase()) : "—";
}

export function speedLabel(speed: string | null | undefined): string {
  const map: Record<string, string> = {
    step: "STEP CHANGE",
    gradual: "GRADUAL",
    reversal: "REVERSAL",
  };
  return speed ? (map[speed] ?? speed.toUpperCase()) : "—";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function polarityColor(polarity: string | null | undefined): string {
  const map: Record<string, string> = {
    positive: "#10b981",
    negative: "#ef4444",
    cautious: "#f59e0b",
    neutral: "#9ca3af",
  };
  return polarity ? (map[polarity] ?? "#9ca3af") : "#9ca3af";
}

export function shiftSignificance(nc: NarrativeChange): "major" | "moderate" | "minor" {
  const d = Math.abs(nc.state_shift.delta ?? 0);
  if (d >= 0.5 || nc.confidence >= 0.90) return "major";
  if (d >= 0.25 || nc.confidence >= 0.75) return "moderate";
  return "minor";
}
