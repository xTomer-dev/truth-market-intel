"use client";

import type { NarrativeChange } from "@/lib/api";
import {
  deltaColor,
  formatDate,
  mechanismLabel,
  shiftSignificance,
  speedLabel,
} from "@/lib/intelligence";
import EvidenceDrawer from "./EvidenceDrawer";
import MarketSignalBadge from "./MarketSignalBadge";
import SentimentBar from "./SentimentBar";

type Props = {
  change: NarrativeChange;
};

export default function TransitionCard({ change }: Props) {
  const sig = shiftSignificance(change);
  const delta = change.state_shift.delta;
  const dColor = deltaColor(delta);

  const sigAccent =
    sig === "major" ? "#10b981" : sig === "moderate" ? "#f59e0b" : "#4b5563";

  return (
    <article className="rounded-lg border border-[#1f2937] bg-[#0d1117] overflow-hidden">
      {/* Header bar */}
      <div
        className="h-0.5 w-full"
        style={{ backgroundColor: sigAccent }}
      />

      <div className="p-5">
        {/* Thread + meta row */}
        <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-[#4b5563]">
              {change.thread_name}
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded border border-[#1f2937] px-1.5 py-0.5 font-mono text-[10px] text-[#6b7280]">
                {mechanismLabel(change.mechanism)}
              </span>
              <span className="rounded border border-[#1f2937] px-1.5 py-0.5 font-mono text-[10px] text-[#6b7280]">
                {speedLabel(change.speed)}
              </span>
              <span className="rounded border border-[#1f2937] px-1.5 py-0.5 font-mono text-[10px] text-[#6b7280]">
                {change.time_period}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div
              className="font-mono text-lg font-bold"
              style={{ color: dColor }}
            >
              {delta != null
                ? (delta >= 0 ? "+" : "") + delta.toFixed(2)
                : "—"}
            </div>
            <div className="text-[10px] text-[#4b5563]">SENTIMENT DELTA</div>
          </div>
        </div>

        {/* State shift */}
        <div className="mb-4 grid grid-cols-[1fr_auto_1fr] items-center gap-2 rounded border border-[#1f2937] bg-[#0f172a] p-3">
          <div>
            <div className="mb-1 text-[9px] uppercase tracking-widest text-[#4b5563]">From</div>
            <SentimentBar score={change.state_shift.from_sentiment} />
            {change.state_shift.from_summary && (
              <p className="mt-1.5 text-[10px] leading-relaxed text-[#6b7280] line-clamp-2">
                {change.state_shift.from_summary}
              </p>
            )}
          </div>
          <div className="text-center text-[#374151] text-xl">→</div>
          <div>
            <div className="mb-1 text-[9px] uppercase tracking-widest text-[#4b5563]">To</div>
            <SentimentBar score={change.state_shift.to_sentiment} />
            {change.state_shift.to_summary && (
              <p className="mt-1.5 text-[10px] leading-relaxed text-[#6b7280] line-clamp-2">
                {change.state_shift.to_summary}
              </p>
            )}
          </div>
        </div>

        {/* Summary */}
        <p className="mb-4 text-sm leading-relaxed text-[#d1d5db]">
          {change.summary}
        </p>

        {/* Bottom row */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <EvidenceDrawer items={change.evidence} />
          <div className="flex flex-wrap items-center gap-3">
            {change.market_signal && (
              <MarketSignalBadge signal={change.market_signal} />
            )}
            <div className="text-right">
              <div className="font-mono text-xs text-[#4b5563]">
                {(change.confidence * 100).toFixed(0)}% conf
              </div>
              <div className="text-[10px] text-[#374151]">
                {formatDate(change.occurred_at)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
