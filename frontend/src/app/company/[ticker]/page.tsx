import Link from "next/link";
import { notFound } from "next/navigation";

import NarrativeItem from "@/components/narrative-item";
import SectionCard from "@/components/section-card";
import { getCompanySummary } from "@/lib/api";

type CompanyPageProps = {
  params: Promise<{ ticker: string }>;
};

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { ticker } = await params;

  try {
    const summary = await getCompanySummary(ticker);

    return (
      <main className="min-h-screen bg-[#f7f7f4] text-black">
        <div className="mx-auto max-w-6xl px-6 py-10">
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
              Company Summary
            </div>
            <h1 className="text-4xl font-semibold tracking-tight">
              {summary.ticker}
            </h1>
            <p className="mt-2 text-base text-black/65">{summary.company_name}</p>
            <div className="mt-4 text-sm text-black/45">
              Latest document ID: {summary.latest_document_id ?? "N/A"}
            </div>
          </header>

          <div className="grid gap-6 lg:grid-cols-3">
            <SectionCard
              title="New Narratives"
              count={summary.summary.new.length}
            >
              {summary.summary.new.length > 0 ? (
                summary.summary.new.map((item) => (
                  <NarrativeItem key={`new-${item.cluster_id}`} item={item} />
                ))
              ) : (
                <EmptyState text="No new narratives detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Repeated Narratives"
              count={summary.summary.repeated.length}
            >
              {summary.summary.repeated.length > 0 ? (
                summary.summary.repeated.map((item) => (
                  <NarrativeItem
                    key={`repeated-${item.cluster_id}`}
                    item={item}
                  />
                ))
              ) : (
                <EmptyState text="No repeated narratives detected." />
              )}
            </SectionCard>

            <SectionCard
              title="Dropped Narratives"
              count={summary.summary.dropped.length}
            >
              {summary.summary.dropped.length > 0 ? (
                summary.summary.dropped.map((item) => (
                  <NarrativeItem key={`dropped-${item.cluster_id}`} item={item} />
                ))
              ) : (
                <EmptyState text="No dropped narratives detected." />
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

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-black/10 bg-black/[0.02] p-4 text-sm text-black/45">
      {text}
    </div>
  );
}
