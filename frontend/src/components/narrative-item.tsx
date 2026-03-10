import { EventDiffItem } from "@/lib/api";

type NarrativeItemProps = {
  item: EventDiffItem;
  tone?: "neutral" | "danger" | "warning" | "success" | "subtle";
};

function toneClasses(tone: NarrativeItemProps["tone"]) {
  switch (tone) {
    case "danger":
      return "border-red-200 bg-red-50";
    case "warning":
      return "border-amber-200 bg-amber-50";
    case "success":
      return "border-emerald-200 bg-emerald-50";
    case "subtle":
      return "border-black/10 bg-black/[0.02]";
    default:
      return "border-black/10 bg-white";
  }
}

export default function NarrativeItem({
  item,
  tone = "neutral",
}: NarrativeItemProps) {
  const firstEvidence = item.evidence[0];

  return (
    <article className={`rounded-xl border p-4 ${toneClasses(tone)}`}>
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-black">
            {item.label || item.cluster_key}
          </div>
          <div className="mt-1 text-xs uppercase tracking-wide text-black/45">
            {item.topic || "Uncategorized"}
          </div>
        </div>

        {item.shift_type ? (
          <div className="rounded-full border border-black/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-black/55">
            {item.shift_type}
          </div>
        ) : null}
      </div>

      {item.canonical_claim_text ? (
        <p className="mb-3 text-sm leading-6 text-black/80">
          {item.canonical_claim_text}
        </p>
      ) : null}

      {firstEvidence ? (
        <div className="rounded-lg border border-black/10 bg-white/80 p-3">
          <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-black/45">
            Latest evidence
          </div>
          <blockquote className="text-sm leading-6 text-black/75">
            “{firstEvidence.source_text || firstEvidence.claim_text}”
          </blockquote>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-black/45">
            <span>{firstEvidence.speaker || "Unknown speaker"}</span>
            {firstEvidence.polarity ? <span>Polarity: {firstEvidence.polarity}</span> : null}
            {firstEvidence.strength ? <span>Strength: {firstEvidence.strength}</span> : null}
          </div>
        </div>
      ) : (
        <div className="text-sm text-black/45">No current-event evidence attached.</div>
      )}
    </article>
  );
}
