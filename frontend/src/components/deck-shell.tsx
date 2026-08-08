"use client";

import { useState } from "react";
import { Archive } from "@/components/archive";
import { PushToggle } from "@/components/push-toggle";
import { RoastStack } from "@/components/roast-stack";
import type { Card } from "@/lib/types";

/** Orchestrates the stack and the archive. Owns overlay state and persistence. */
export function DeckShell({ cards }: { cards: Card[] }) {
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [detail, setDetail] = useState<Card | null>(null);
  const [filed, setFiled] = useState<Set<string>>(new Set());

  const unread = cards.filter((card) => !card.viewed);
  const remaining = unread.filter((card) => !filed.has(card.id)).length;

  function handleFile(card: Card, published: boolean) {
    setFiled((prev) => new Set(prev).add(card.id));

    fetch("/api/viewed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: card.id, published }),
    }).catch((error) => console.error("mark viewed failed", error));
  }

  return (
    <>
      <main className="flex min-h-dvh flex-col items-center justify-center px-5 py-16">
         <div className="fixed inset-x-0 top-0 flex items-center justify-between px-5 py-4 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-desk-dim">
          <button onClick={() => setArchiveOpen(true)}>
            All {cards.length}
          </button>
          <PushToggle />
          <span>{remaining > 0 ? `${remaining} unread` : "Clear"}</span>
        </div>

        <div className="w-full max-w-sm animate-card-in">
          <RoastStack cards={unread} onFile={handleFile} />
        </div>

        {remaining > 0 && (
          <p className="fixed bottom-6 font-mono text-[0.58rem] uppercase tracking-[0.2em] text-desk-dim">
            Left to file · Right to publish
          </p>
        )}
      </main>

      {archiveOpen && (
        <Archive
          cards={cards}
          detail={detail}
          onOpen={setDetail}
          onCloseDetail={() => setDetail(null)}
          onClose={() => {
            setDetail(null);
            setArchiveOpen(false);
          }}
        />
      )}
    </>
  );
}