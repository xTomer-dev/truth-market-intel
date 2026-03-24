"use client";

import { useState } from "react";
import type { NarrativeThreadDetail, ThreadState } from "@/lib/api";
import { getThreadStates } from "@/lib/api";
import { formatDate, sentimentColor } from "@/lib/intelligence";
import SentimentBar from "./SentimentBar";

type Props = {
  thread: NarrativeThreadDetail;
  ticker: string;
};

// SVG sparkline from array of {x, y} points (x in [0,1], y in [0,1])
function Sparkline({
  scores,
  width = 120,
  height = 32,
}: {
  scores: number[];
  width?: number;
  height?: number;
}) {
  if (scores.length < 2) return null;

  const min = -1;
  const max = 1;
  const range = max - min;

  const points = scores.map((s, i) => {
    const x = (i / (scores.length - 1)) * width;
    const y = height - ((s - min) / range) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const lastScore = scores[scores.length - 1];
  const color = sentimentColor(lastScore);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="overflow-visible"
    >
      {/* zero line */}
      <line
        x1="0"
        y1={height / 2}
        x2={width}
        y2={height / 2}
        stroke="#1f2937"
        strokeWidth="1"
        strokeDasharray="3 3"
      />
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* endpoint dot */}
      <circle
        cx={parseFloat(points[points.length - 1].split(",")[0])}
        cy={parseFloat(points[points.length - 1].split(",")[1])}
        r="2.5"
        fill={color}
      />
    </svg>
  );
}

export default function ThreadTimeline({ thread, ticker }: Props) {
  const [states, setStates] = useState<ThreadState[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  async function toggle() {
    if (!expanded && states === null) {
      setLoading(true);
      try {
        const res = await getThreadStates(ticker, thread.id);
        setStates(res.states);
      } catch {
        setStates([]);
      } finally {
        setLoading(false);
      }
    }
    setExpanded((v) => !v);
  }

  const latest = thread.latest_state;
  const scores = states ? states.map((s) => s.sentiment_score) : [];

  return (
    <div className="border-b border-[#1f2937] last:border-0">
      <button
        onClick={toggle}
        className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left transition hover:bg-[#0f172a]"
      >
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-medium text-[#e5e7eb]">
            {thread.name}
          </div>
          <div className="mt-0.5 flex items-center gap-3">
            {thread.kpi_label && (
              <span className="text-[10px] text-[#4b5563]">{thread.kpi_label}</span>
            )}
            {latest && (
              <span className="font-mono text-[10px] text-[#6b7280]">{latest.time_period}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          {scores.length >= 2 && <Sparkline scores={scores} />}
          {latest && <SentimentBar score={latest.sentiment_score} />}
          <span className="text-[#374151] text-sm">{expanded ? "−" : "+"}</span>
        </div>
      </button>

      <div
        className="overflow-hidden transition-all duration-200"
        style={{ maxHeight: expanded ? "800px" : "0px" }}
      >
        {loading && (
          <div className="px-4 py-3 text-xs text-[#4b5563]">Loading…</div>
        )}
        {states && states.length === 0 && (
          <div className="px-4 py-3 text-xs text-[#4b5563]">No states recorded.</div>
        )}
        {states && states.length > 0 && (
          <div className="space-y-0">
            {states.map((state, i) => (
              <div
                key={state.id}
                className="flex gap-4 px-4 py-3 text-xs border-t border-[#1f2937]"
              >
                <div className="flex flex-col items-center">
                  <div
                    className="h-2 w-2 rounded-full mt-1"
                    style={{ backgroundColor: sentimentColor(state.sentiment_score) }}
                  />
                  {i < states.length - 1 && (
                    <div className="mt-1 w-px flex-1 bg-[#1f2937]" />
                  )}
                </div>
                <div className="flex-1 pb-2">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-[10px] text-[#4b5563]">
                      {state.time_period}
                    </span>
                    <SentimentBar score={state.sentiment_score} />
                  </div>
                  <p className="text-[#9ca3af] leading-relaxed">{state.summary}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
