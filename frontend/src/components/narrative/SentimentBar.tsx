"use client";

import { sentimentColor } from "@/lib/intelligence";

type SentimentBarProps = {
  score: number | null | undefined;
  showLabel?: boolean;
};

export default function SentimentBar({ score, showLabel = true }: SentimentBarProps) {
  if (score == null) return <span className="text-[#4b5563] text-xs">—</span>;

  // Normalize score from [-1, 1] to [0, 100]
  const pct = Math.round(((score + 1) / 2) * 100);
  const color = sentimentColor(score);
  const label = score >= 0 ? `+${score.toFixed(2)}` : score.toFixed(2);

  return (
    <div className="flex items-center gap-2">
      <div className="relative h-1.5 w-24 rounded-full bg-[#1f2937] overflow-hidden">
        {/* center marker */}
        <div className="absolute left-1/2 top-0 h-full w-px bg-[#374151]" />
        {/* fill from center */}
        {score >= 0 ? (
          <div
            className="absolute top-0 h-full rounded-full"
            style={{
              left: "50%",
              width: `${(score / 1) * 50}%`,
              backgroundColor: color,
            }}
          />
        ) : (
          <div
            className="absolute top-0 h-full rounded-full"
            style={{
              right: "50%",
              width: `${(Math.abs(score) / 1) * 50}%`,
              backgroundColor: color,
            }}
          />
        )}
      </div>
      {showLabel && (
        <span className="font-mono text-xs" style={{ color }}>
          {label}
        </span>
      )}
    </div>
  );
}
