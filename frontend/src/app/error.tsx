"use client";

export default function ErrorPage() {
  return (
    <main className="min-h-screen bg-[#f7f7f4] text-black">
      <div className="mx-auto max-w-3xl px-6 py-16">
        <div className="rounded-2xl border border-red-200 bg-white p-6 shadow-sm">
          <div className="text-sm font-medium uppercase tracking-wide text-red-600">
            Error
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            Failed to load narrative intelligence.
          </h1>
          <p className="mt-3 text-black/65">
            Check that the FastAPI backend is running on
            <span className="mx-1 font-medium">http://127.0.0.1:8000</span>
            and try again.
          </p>
        </div>
      </div>
    </main>
  );
}
