import Link from "next/link";

import { getCompanies } from "@/lib/api";

export default async function HomePage() {
  const companies = await getCompanies();

  return (
    <main className="min-h-screen bg-[#f7f7f4] text-black">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-12">
          <div className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-black/45">
            Truth Market Intel
          </div>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
            Financial narrative intelligence for public markets.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-black/65">
            Explore earnings-call narrative shifts, clustered claims, and
            evidence-backed company summaries.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {companies.map((company) => (
            <Link
              key={company.id}
              href={`/company/${company.ticker}`}
              className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="text-xs uppercase tracking-wide text-black/45">
                {company.sector || "Unknown sector"}
              </div>
              <div className="mt-2 text-2xl font-semibold">{company.ticker}</div>
              <div className="mt-1 text-sm leading-6 text-black/65">
                {company.name}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
