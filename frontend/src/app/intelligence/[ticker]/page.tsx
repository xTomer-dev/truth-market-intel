import Link from "next/link";
import { notFound } from "next/navigation";

import { getNarrativeBrief, getThreads } from "@/lib/api";
import IntelligenceClient from "./client";

type Props = {
  params: Promise<{ ticker: string }>;
};

export default async function IntelligencePage({ params }: Props) {
  const { ticker } = await params;
  const t = ticker.toUpperCase();

  let brief, threadsData;
  try {
    [brief, threadsData] = await Promise.all([
      getNarrativeBrief(t, { limit: 15, min_confidence: 0.5 }),
      getThreads(t),
    ]);
  } catch {
    notFound();
  }

  const { counts } = brief;

  return (
    <main className="min-h-screen bg-[#060b14] text-[#e5e7eb]">
      <div className="mx-auto max-w-[1400px] px-6 py-8">

        {/* Nav */}
        <div className="mb-8 flex items-center gap-6 text-xs text-[#4b5563]">
          <Link href="/" className="transition hover:text-[#9ca3af]">
            ← Home
          </Link>
          <span>/</span>
          <Link href={`/company/${t}`} className="transition hover:text-[#9ca3af]">
            Event Diff
          </Link>
          <span>/</span>
          <span className="text-[#6b7280]">Intelligence</span>
        </div>

        {/* Header */}
        <header className="mb-8 border-b border-[#1f2937] pb-6">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-[#374151]">
            Narrative Intelligence
          </div>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-4xl font-semibold tracking-tight text-white">
                {brief.company.ticker}
              </h1>
              <p className="mt-1 text-base text-[#6b7280]">{brief.company.name}</p>
            </div>
            <div className="text-right text-xs text-[#374151]">
              <div>
                {new Date(brief.window_start).toLocaleDateString("en-US", {
                  year: "numeric", month: "short", day: "numeric",
                })}
                {" — "}
                {new Date(brief.window_end).toLocaleDateString("en-US", {
                  year: "numeric", month: "short", day: "numeric",
                })}
              </div>
              <div className="mt-0.5 text-[#2d3748]">
                Generated {new Date(brief.generated_at).toLocaleTimeString("en-US", {
                  hour: "2-digit", minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        </header>

        {/* Summary strip */}
        <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricTile label="Transitions" value={counts.total_transitions} />
          <MetricTile label="With Evidence" value={counts.with_evidence} />
          <MetricTile label="Market Signals" value={counts.with_market_signal} />
          <MetricTile label="Active Threads" value={counts.threads_active} />
        </div>

        {/* Main content */}
        <IntelligenceClient
          brief={brief}
          threads={threadsData.threads}
          ticker={t}
        />
      </div>
    </main>
  );
}

function MetricTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-[#1f2937] bg-[#0d1117] px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-[#374151]">
        {label}
      </div>
      <div className="mt-1.5 font-mono text-2xl font-semibold text-white">
        {value}
      </div>
    </div>
  );
}
