export default function Loading() {
  return (
    <main className="min-h-screen bg-[#f7f7f4] text-black">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-4 w-32 rounded bg-black/10" />
          <div className="h-10 w-96 rounded bg-black/10" />
          <div className="h-6 w-[32rem] rounded bg-black/10" />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="h-72 rounded-2xl bg-white shadow-sm" />
            <div className="h-72 rounded-2xl bg-white shadow-sm" />
            <div className="h-72 rounded-2xl bg-white shadow-sm" />
          </div>
        </div>
      </div>
    </main>
  );
}
