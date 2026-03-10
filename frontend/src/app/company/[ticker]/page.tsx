import Link from "next/link";
import { notFound } from "next/navigation";

import NarrativeItem from "@/components/narrative-item";
import SectionCard from "@/components/section-card";
import { getEventDiff } from "@/lib/api";

type CompanyPageProps = {
  params: Promise<{ ticker: string }>;
};

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { ticker } = await params;

  try {
    const diff = await getEventDiff(ticker, "earnings_call");

    return (
      <main className="min-h-screen bg-[#f7f7f4] text-black">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <div className="mb-8">
            <Link
              href="/"
              className="text-sm text-black/45 transition hover:text-black"
            >
              ← Back
            </Link>
          </div>

          <header className="mb-10 rounded-3xl border border-black/10 bg-white p-6 shadow-sm">
            <div className="mb-2 text-xs font-medium uppercase tracking-[0.2em] text-black/45">
              Event Diff
            </div>
            <h1 className="text-4xl font-semibold tracking-tight">
              {diff.ticker}
            </h1>
            <p className="mt-2 text-base text-black/65">{diff.company_name}</p>

            <div className="mt-5 flex flex-wrap gap-4 text-sm text-black/45">
              <span>Family: {diff.comparison_family || "N/A"}</span>
              <span>Latest document: {diff.latest_document_id ?? "N/A"}</span>
              <span>Previous document: {diff.previous_document_id ?? "N/A"}</span>
            </div>
          </header>

          <div className="mb-6 grid gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Metric label="Contradicted" value={diff.event_diff.contradicted.length} />
            <Metric label="Weakened" value={diff.event_diff.weakened.length} />
            <Metric label="Strengthened" value={diff.event_diff.strengthened.length} />
            <Metric label="New" value={diff.event_diff.new.length} />
            <Metric label="Dropped" value={diff.event_diff.dropped.length} />
            <Metric label="Repeated" value={diff.event_diff.repeated.length} />
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard
              title="Contradictions"
              count={diff.event_diff.contradicted.length}
            >
              {diff.event_diff.contradicted.length > 0 ? (
                diff.event_diff.contradicted.map((item) => (
                  <NarrativeItem
                    key={`contradicted-${item.cluster_id}`}
                    item={item}
                    tone="danger"
                  />
                ))
              ) : (
                <EmptyState text="No contradictions detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Weakened"
              count={diff.event_diff.weakened.length}
            >
              {diff.event_diff.weakened.length > 0 ? (
                diff.event_diff.weakened.map((item) => (
                  <NarrativeItem
                    key={`weakened-${item.cluster_id}`}
                    item={item}
                    tone="warning"
                  />
                ))
              ) : (
                <EmptyState text="No weakened narratives detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Strengthened"
              count={diff.event_diff.strengthened.length}
            >
              {diff.event_diff.strengthened.length > 0 ? (
                diff.event_diff.strengthened.map((item) => (
                  <NarrativeItem
                    key={`strengthened-${item.cluster_id}`}
                    item={item}
                    tone="success"
                  />
                ))
              ) : (
                <EmptyState text="No strengthened narratives detected." />
              )}
            </SectionCard>

            <SectionCard title="New" count={diff.event_diff.new.length}>
              {diff.event_diff.new.length > 0 ? (
                diff.event_diff.new.map((item) => (
                  <NarrativeItem
                    key={`new-${item.cluster_id}`}
                    item={item}
                    tone="neutral"
                  />
                ))
              ) : (
                <EmptyState text="No new narratives detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Dropped"
              count={diff.event_diff.dropped.length}
            >
              {diff.event_diff.dropped.length > 0 ? (
                diff.event_diff.dropped.map((item) => (
                  <NarrativeItem
                    key={`dropped-${item.cluster_id}`}
                    item={item}
                    tone="subtle"
                  />
                ))
              ) : (
                <EmptyState text="No dropped narratives detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Repeated"
              count={diff.event_diff.repeated.length}
            >
              {diff.event_diff.repeated.length > 0 ? (
                diff.event_diff.repeated.map((item) => (
                  <NarrativeItem
                    key={`repeated-${item.cluster_id}`}
                    item={item}
                    tone="subtle"
                  />
                ))
              ) : (
                <EmptyState text="No repeated narratives detected." />
              )}
            </SectionCard>
          </div>
        </div>
      </main>
    );
  } catch {
    notFound();
  }
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white p-4 shadow-sm">
      <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-black/45">
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-black/10 bg-black/[0.02] p-4 text-sm text-black/45">
      {text}
    </div>
  );
}
