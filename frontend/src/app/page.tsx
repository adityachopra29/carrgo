"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Phone,
  ShieldCheck,
  Radio,
  Truck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

const features = [
  {
    icon: Phone,
    title: "Parallel carrier calls",
    description:
      "AI voice agents reach dozens of compliant carriers at once — no more manual dial lists.",
  },
  {
    icon: ShieldCheck,
    title: "Built-in compliance",
    description:
      "Every carrier is filtered for authority, insurance, and equipment match before a single call goes out.",
  },
  {
    icon: Radio,
    title: "Live quote stream",
    description:
      "Watch rates roll in on your dashboard in real time as negotiations happen on the line.",
  },
];

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-amber-100/60 blur-3xl" />
        <div className="absolute top-1/3 -right-24 h-72 w-72 rounded-full bg-sky-100/50 blur-3xl" />
        <div className="absolute bottom-0 -left-16 h-64 w-64 rounded-full bg-orange-100/40 blur-3xl" />
      </div>

      <header className="relative z-10 border-b border-border/60 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <span className="flex size-8 items-center justify-center rounded-lg bg-amber-500 text-white">
              <Truck className="size-4" />
            </span>
            Carrgo
          </Link>
          <div className="flex items-center gap-3">
            <Button variant="ghost" render={<Link href="/login" />}>
              Sign in
            </Button>
            <Button render={<Link href="/register" />}>
              Get started
            </Button>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <section className="mx-auto max-w-6xl px-6 pb-24 pt-20 md:pt-28">
          <div className="mx-auto max-w-3xl text-center">
            <p className="mb-6 inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-4 py-1.5 text-sm font-medium text-amber-800">
              AI-powered freight brokering
            </p>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl md:leading-[1.1]">
              Stop being stopped by brokers.
              <span className="mt-2 block text-amber-600">
                Start booking in an instant.
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
              Post a load, set your rates, and let Carrgo call compliant carriers
              in parallel — streaming live quotes straight to your dashboard.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" className="h-11 px-6" render={<Link href="/register" />}>
                Start booking free
                <ArrowRight className="ml-1 size-4" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="h-11 px-6"
                render={<Link href="/login" />}
              >
                Sign in to your account
              </Button>
            </div>
          </div>

          <div className="mx-auto mt-20 max-w-4xl rounded-2xl border bg-card p-2 shadow-lg shadow-amber-500/5">
            <div className="rounded-xl border bg-muted/30 p-6 md:p-8">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Live outreach
                  </p>
                  <p className="text-lg font-semibold">
                    Chicago, IL → Dallas, TX
                  </p>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                  <span className="size-1.5 animate-pulse rounded-full bg-emerald-500" />
                  12 calls active
                </span>
              </div>
              <div className="space-y-3">
                {[
                  { carrier: "Midwest Freight Co.", rate: "$2,450", status: "Quoted" },
                  { carrier: "Heartland Logistics", rate: "$2,380", status: "Quoted" },
                  { carrier: "Prairie Line Transport", rate: "Negotiating…", status: "On call" },
                ].map((row) => (
                  <div
                    key={row.carrier}
                    className="flex items-center justify-between rounded-lg border bg-background px-4 py-3"
                  >
                    <span className="text-sm font-medium">{row.carrier}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm font-semibold tabular-nums">
                        {row.rate}
                      </span>
                      <span
                        className={
                          row.status === "Quoted"
                            ? "text-xs font-medium text-emerald-600"
                            : "text-xs font-medium text-amber-600"
                        }
                      >
                        {row.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="border-t bg-muted/20">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <div className="mb-12 text-center">
              <h2 className="text-2xl font-bold md:text-3xl">
                Everything between post and book
              </h2>
              <p className="mt-3 text-muted-foreground">
                Carrgo handles outreach, compliance, and negotiation so you can
                focus on closing loads.
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="mb-4 flex size-10 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                    <Icon className="size-5" />
                  </div>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-20">
          <div className="rounded-2xl bg-amber-500 px-8 py-12 text-center text-white md:px-16">
            <h2 className="text-2xl font-bold md:text-3xl">
              Ready to book faster?
            </h2>
            <p className="mx-auto mt-3 max-w-md text-amber-50">
              Create your account and post your first load in minutes.
            </p>
            <Button
              size="lg"
              variant="secondary"
              className="mt-8 h-11 bg-white px-6 text-amber-700 hover:bg-amber-50"
              render={<Link href="/register" />}
            >
              Get started
              <ArrowRight className="ml-1 size-4" />
            </Button>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Carrgo</span>
          <span>AI freight brokering automation</span>
        </div>
      </footer>
    </div>
  );
}
