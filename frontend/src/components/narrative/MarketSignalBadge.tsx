import type { MarketSignal } from "@/lib/api";

type Props = { signal: MarketSignal };

export default function MarketSignalBadge({ signal }: Props) {
  const move = signal.price_move_pct;
  if (move == null) return null;

  const positive = move >= 0;
  const color = positive ? "#10b981" : "#ef4444";
  const prefix = positive ? "+" : "";

  return (
    <div className="flex items-center gap-3 rounded border border-[#1f2937] bg-[#111827]/60 px-3 py-1.5">
      <span className="font-mono text-sm font-semibold" style={{ color }}>
        {prefix}{move.toFixed(1)}%
      </span>
      {signal.volume_vs_avg != null && (
        <span className="text-xs text-[#6b7280]">
          {signal.volume_vs_avg.toFixed(1)}× vol
        </span>
      )}
      {signal.options_iv_spike && (
        <span className="rounded bg-[#f59e0b]/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[#f59e0b]">
          IV spike
        </span>
      )}
    </div>
  );
}
