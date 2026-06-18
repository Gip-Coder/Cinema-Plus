import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center gap-8 px-6 py-16">
        <div className="space-y-4">
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Phase 3.5 Step 1
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-normal text-foreground sm:text-5xl">
            Cinema Plus Next.js foundation
          </h1>
          <p className="max-w-2xl text-base leading-7 text-muted-foreground">
            The application shell is ready for incremental migration with Next.js 15,
            TypeScript, Tailwind CSS, shadcn/ui, Zustand, and TanStack Query.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button>Frontend shell ready</Button>
          <Button variant="outline">Pages not migrated yet</Button>
        </div>
      </section>
    </main>
  );
}
