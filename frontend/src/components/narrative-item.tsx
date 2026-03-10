import { NarrativeCluster } from "@/lib/api";

type NarrativeItemProps = {
  item: NarrativeCluster;
};

export default function NarrativeItem({ item }: NarrativeItemProps) {
  const firstEvidence = item.evidence[0];

  return (
    <article className="rounded-xl border border-black/10 bg-black/[0.02] p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-black">
            {item.label || item.cluster_key}
          </div>
          <div className="mt-1 text-xs uppercase tracking-wide text-black/45">
            {item.topic || "Uncategorized"}
          </div>
        </div>
      </div>

      {item.canonical_claim_text ? (
        <p className="mb-3 text-sm leading-6 text-black/80">
          {item.canonical_claim_text}
        </p>
      ) : null}

      {firstEvidence ? (
        <div className="rounded-lg border border-black/10 bg-white p-3">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-black/45">
            Supporting evidence
          </div>
          <blockquote className="text-sm leading-6 text-black/75">
            “{firstEvidence.source_text || firstEvidence.claim_text}”
          </blockquote>
          <div className="mt-3 text-xs text-black/45">
            {firstEvidence.speaker || "Unknown speaker"}
          </div>
        </div>
      ) : (
        <div className="text-sm text-black/45">No evidence attached.</div>
      )}
    </article>
  );
}
