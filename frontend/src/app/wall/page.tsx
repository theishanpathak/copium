import type { Metadata } from "next";
import { RoastCard } from "@/components/roast-card";
import { supabase } from "@/lib/supabase";
import type { Card } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Copium · The wall",
  description: "Job rejections, roasted automatically.",
};

export default async function Wall() {
  const { data } = await supabase
    .from("rejections")
    .select(
      "id, message_id, company_name, role, roast, rejection_quote, received_at",
    )
    .eq("published", true)
    .order("created_at", { ascending: false });

  const rows = data ?? [];

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

  return (
    <main className="mx-auto max-w-sm px-5 py-14">
      <header className="pb-10 text-center">
        <p className="font-mono text-[0.62rem] uppercase tracking-[0.24em] text-stamp">
          Copium
        </p>
        <p className="mt-3 text-sm text-desk-dim">
          Every rejection I get is read, researched, and roasted automatically.
          These are the ones worth keeping.
        </p>
      </header>

      {cards.length === 0 ? (
        <p className="py-16 text-center font-mono text-[0.62rem] uppercase tracking-[0.18em] text-desk-dim">
          Nothing published yet
        </p>
      ) : (
        <div className="flex flex-col gap-8">
          {cards.map((card) => (
            <RoastCard key={card.id} card={card} />
          ))}
        </div>
      )}

      <footer className="pt-14 text-center font-mono text-[0.58rem] uppercase tracking-[0.18em] text-desk-dim">
        Built with Gmail, LangGraph, and poor timing
      </footer>
    </main>
  );
}