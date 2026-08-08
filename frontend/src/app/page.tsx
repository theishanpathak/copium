import { DeckShell } from "@/components/deck-shell";
import { supabase } from "@/lib/supabase";
import type { Card } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const { data } = await supabase
    .from("rejections")
    .select(
      "id, company_name, role, roast, rejection_quote, received_at, viewed_at, published",
    )
    .order("created_at", { ascending: false });

  const rows = data ?? [];
  const total = rows.length;

  const cards: Card[] = rows.map((row, index) => ({
    id: row.id,
    company: row.company_name,
    role: row.role,
    roast: row.roast,
    quote: row.rejection_quote,
    receivedAt: row.received_at,
    seq: total - index,
    viewed: row.viewed_at !== null,
    published: row.published,
  }));

  return <DeckShell cards={cards} />;
}