"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Archive } from "@/components/archive";
import { PushToggle } from "@/components/push-toggle";
import { RoastStack } from "@/components/roast-stack";
import type { Card } from "@/lib/types";

/** Orchestrates the stack and the archive. Owns overlay state and persistence. */
export function DeckShell({ cards }: { cards: Card[] }) {
  const router = useRouter();

  const [archiveOpen, setArchiveOpen] = useState(false);
  const [detail, setDetail] = useState<Card | null>(null);
  const [filed, setFiled] = useState<Set<string>>(new Set());

  const unread = cards.filter((card) => !card.viewed);

  // Identity of the current server data. Changes only when a refresh brings a
  // different set of unread cards, never on a swipe.
  const stackKey = unread.map((card) => card.id).join(",");

  // Tapping a notification focuses an already-open window rather than
  // reloading it, so the page would otherwise show data from before the card
  // existed. Refetch whenever the app comes back to the foreground.
  useEffect(() => {
    function onVisibility() {
      if (document.visibilityState === "visible") router.refresh();
    }

    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [router]);

  // The service worker posts this when a push arrives, so a card appears in a
  // foregrounded app without waiting for a visibility change.
  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.data?.type === "new-card") router.refresh();
    }

    navigator.serviceWorker?.addEventListener("message", onMessage);
    return () =>
      navigator.serviceWorker?.removeEventListener("message", onMessage);
  }, [router]);

  // A refresh drops swiped cards out of `unread`, so the session's filed set is
  // spent and RoastStack's internal index would point past the end.
  useEffect(() => {
    setFiled(new Set());
  }, [stackKey]);

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
          <RoastStack key={stackKey} cards={unread} onFile={handleFile} />
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