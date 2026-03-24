"use client";

import type { NarrativeBrief, NarrativeThreadDetail } from "@/lib/api";
import TransitionCard from "@/components/narrative/TransitionCard";
import ThreadTimeline from "@/components/narrative/ThreadTimeline";

type Props = {
  brief: NarrativeBrief;
  threads: NarrativeThreadDetail[];
  ticker: string;
};

export default function IntelligenceClient({ brief, threads, ticker }: Props) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      {/* Left: narrative changes feed */}
      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#4b5563]">
            Narrative Changes
          </h2>
          <span className="font-mono text-xs text-[#374151]">
            {brief.narrative_changes.length} transition{brief.narrative_changes.length !== 1 ? "s" : ""}
          </span>
        </div>

        {brief.narrative_changes.length === 0 ? (
          <div className="rounded-lg border border-dashed border-[#1f2937] p-8 text-center text-sm text-[#4b5563]">
            No narrative changes in the selected window.
          </div>
        ) : (
          <div className="space-y-4">
            {brief.narrative_changes.map((change) => (
              <TransitionCard key={change.transition_id} change={change} />
            ))}
          </div>
        )}
      </section>

      {/* Right: thread trajectories */}
      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[#4b5563]">
            Thread Trajectories
          </h2>
          <span className="font-mono text-xs text-[#374151]">
            {threads.length} thread{threads.length !== 1 ? "s" : ""}
          </span>
        </div>

        {threads.length === 0 ? (
          <div className="rounded-lg border border-dashed border-[#1f2937] p-6 text-center text-sm text-[#4b5563]">
            No threads tracked yet.
          </div>
        ) : (
          <div className="rounded-lg border border-[#1f2937] bg-[#0d1117] divide-y divide-[#1f2937] overflow-hidden">
            {threads.map((thread) => (
              <ThreadTimeline key={thread.id} thread={thread} ticker={ticker} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
