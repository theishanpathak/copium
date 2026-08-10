import type { Metadata } from "next";
import { RoastCard } from "@/components/roast-card";
import { supabase } from "@/lib/supabase";
import type { Card } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Copium · rejections, roasted",
  description:
    "Every job rejection I get is read, researched, and roasted automatically.",
};

/** Pinned to the top in this order. Everything else is shuffled, because
 *  chronology means nothing to a first-time visitor and the stronger cards
 *  should not always end up at the bottom. */
const PINNED = [
  "9b29d1c2-17c8-490a-b765-97cc4393112f",
  "c7c66782-71da-4ea0-b8a3-2ea2319fab07",
  "8de4dc93-2317-4c3f-a049-00b32bca700e",
];

const PIPELINE = [
  ["Gmail push", "A notification the moment mail arrives. No polling."],
  ["Classify", "Rejection, interview invite, acknowledgment, or noise."],
  ["Extract", "Which company, which role."],
  ["Research", "What that company has actually been doing lately."],
  ["Roast", "Two sentences about what turned up."],
  ["My phone", "Card lands about thirty seconds after the email."],
];

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

/** The pipeline timeline. Rendered inside a disclosure on mobile and in the
 *  sidebar on desktop, so it lives here rather than being written twice. */
function Pipeline() {
  return (
    <>
      <ol className="border-l border-white/10">
        {PIPELINE.map(([stage, note]) => (
          <li key={stage} className="relative pb-6 pl-5 last:pb-0">
            <span
              aria-hidden
              className="absolute -left-[3px] top-1.5 size-[5px] rounded-full bg-stamp"
            />
            <p className="font-mono text-[0.6rem] uppercase tracking-[0.16em]">
              {stage}
            </p>
            <p className="mt-1.5 text-[0.8rem] leading-relaxed text-desk-dim text-pretty">
              {note}
            </p>
          </li>
        ))}
      </ol>

      <p className="mt-8 border-t border-white/10 pt-6 text-[0.8rem] leading-relaxed text-desk-dim text-pretty">
        Interview invites skip the joke and just buzz my phone. Everything else
        gets filed quietly.
      </p>
    </>
  );
}

export default async function Wall() {
  const [publishedResult, countResult] = await Promise.all([
    supabase
      .from("rejections")
      .select(
        "id, message_id, company_name, role, roast, rejection_quote, received_at",
      )
      .eq("published", true)
      .order("created_at", { ascending: false }),
    supabase
      .from("processed_messages")
      .select("message_id", { count: "exact", head: true }),
  ]);

  const rows = publishedResult.data ?? [];
  const processed = countResult.count ?? 0;

  const cards: Card[] = rows.map((row, index) => ({
    id: row.id,
    messageId: row.message_id,
    company: row.company_name,
    role: row.role,
    roast: row.roast,
    quote: row.rejection_quote,
    receivedAt: row.received_at,
    seq: rows.length - index,
    viewed: true,
    published: true,
  }));

  // A pinned id that is not published simply drops out rather than breaking.
  const pinned = PINNED.map((id) => cards.find((card) => card.id === id)).filter(
    (card): card is Card => card !== undefined,
  );

  const ordered = [
    ...pinned,
    ...shuffle(cards.filter((card) => !PINNED.includes(card.id))),
  ];

  return (
    <div className="mx-auto max-w-[100rem] px-5 pb-24 pt-14 lg:px-10 lg:pt-20">
      <header className="border-b border-white/10 pb-10">
        <p className="font-mono text-[0.62rem] uppercase tracking-[0.28em] text-stamp">
          Copium
        </p>

        <div className="mt-6 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <h1 className="text-[1.75rem] font-semibold leading-[1.15] tracking-tight text-balance lg:text-[2.5rem]">
              Every job rejection I get is read, researched, and roasted
              automatically.
            </h1>

            <p className="mt-4 max-w-xl text-sm leading-relaxed text-desk-dim text-pretty lg:text-base">
              A rejection lands in Gmail and a card is on my phone about thirty
              seconds later. No part of this is written by hand. These are the
              ones I thought were worth keeping.
            </p>
          </div>

          <dl className="flex shrink-0 gap-10">
            <div>
              <dt className="font-mono text-[0.55rem] uppercase tracking-[0.2em] text-desk-dim">
                Emails handled
              </dt>
              <dd className="mt-1.5 text-3xl font-semibold tabular-nums">
                {processed}
              </dd>
            </div>
            <div>
              <dt className="font-mono text-[0.55rem] uppercase tracking-[0.2em] text-desk-dim">
                Published
              </dt>
              <dd className="mt-1.5 text-3xl font-semibold tabular-nums text-stamp">
                {cards.length}
              </dd>
            </div>
          </dl>
        </div>
      </header>

      {/* Native disclosure, so mobile gets a tappable summary with no client JS. */}
      <details className="group border-b border-white/10 lg:hidden">
        <summary className="flex cursor-pointer list-none items-center justify-between py-4 font-mono text-[0.6rem] uppercase tracking-[0.24em] text-stamp [&::-webkit-details-marker]:hidden">
          How it works
          <span
            aria-hidden
            className="text-desk-dim transition-transform duration-200 group-open:rotate-45"
          >
            +
          </span>
        </summary>

        <div className="pb-8 pt-2">
          <Pipeline />
        </div>
      </details>

      <div className="mt-12 grid gap-12 lg:grid-cols-[1fr_17rem] lg:gap-14">
        <section>
          {ordered.length === 0 ? (
            <p className="py-24 text-center font-mono text-[0.62rem] uppercase tracking-[0.18em] text-desk-dim">
              Nothing published yet
            </p>
          ) : (
            <div className="grid auto-rows-fr gap-6 [grid-template-columns:repeat(auto-fill,minmax(20rem,1fr))]">
              {ordered.map((card) => (
                <RoastCard key={card.id} card={card} />
              ))}
            </div>
          )}
        </section>

        <aside className="hidden lg:sticky lg:top-14 lg:block lg:self-start">
          <h2 className="mb-6 font-mono text-[0.6rem] uppercase tracking-[0.24em] text-stamp">
            How it works
          </h2>
          <Pipeline />
        </aside>
      </div>

      <footer className="mt-20 flex flex-wrap items-baseline justify-between gap-4 border-t border-white/10 pt-8 font-mono text-[0.6rem] uppercase tracking-[0.16em] text-desk-dim">
        <span>Still available, incidentally</span>
        <a
          href="https://theishanpathak.com"
          className="text-paper underline decoration-white/25 underline-offset-4 hover:decoration-paper"
        >
          theishanpathak.com
        </a>
      </footer>
    </div>
  );
}