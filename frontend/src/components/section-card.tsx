import { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  count?: number;
  children: ReactNode;
};

export default function SectionCard({
  title,
  count,
  children,
}: SectionCardProps) {
  return (
    <section className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-wide text-black/80 uppercase">
          {title}
        </h2>
        {typeof count === "number" ? (
          <span className="rounded-full border border-black/10 px-2 py-0.5 text-xs text-black/60">
            {count}
          </span>
        ) : null}
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  );
}
