"use client";

import { RoastCard } from "@/components/roast-card";
import { sequence } from "@/lib/format";
import type { Card } from "@/lib/types";

type Props = {
  cards: Card[];
  detail: Card | null;
  onOpen: (card: Card) => void;
  onCloseDetail: () => void;
  onClose: () => void;
};

/** Full-screen grid of every card, with a tap-to-enlarge detail view. */
export function Archive({
  cards,
  detail,
  onOpen,
  onCloseDetail,
  onClose,
}: Props) {
  return (
    <>
      <div className="fixed inset-0 z-10 overflow-y-auto bg-desk px-4 pb-16 pt-6">
        <div className="mx-auto flex max-w-2xl items-baseline justify-between pb-4 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-desk-dim">
          <span>Archive · {cards.length}</span>
          <button onClick={onClose} className="uppercase tracking-[0.2em]">
            Close
          </button>
        </div>

        <div className="mx-auto grid max-w-2xl grid-cols-2 gap-2.5 sm:grid-cols-3">
          {cards.map((card) => (
            <button
              key={card.id}
              onClick={() => onOpen(card)}
              className="flex aspect-4/5 flex-col justify-between rounded-lg bg-paper px-3 py-2.5 text-left text-ink"
            >
              <span className="font-mono text-[0.55rem] uppercase tracking-[0.16em] text-ink-soft">
                {sequence(card.seq)}
              </span>
              <span className="text-base font-bold leading-[0.95] tracking-tight">
                {card.company}
              </span>
              <span className="font-mono text-[0.5rem] uppercase tracking-[0.16em] text-stamp">
                {!card.viewed ? "Unread" : card.published ? "Published" : ""}
              </span>
            </button>
          ))}
        </div>
      </div>

      {detail && (
        <div
          className="fixed inset-0 z-20 flex items-center justify-center bg-black/85 p-5"
          onClick={onCloseDetail}
        >
          <div
            className="w-full max-w-sm animate-card-in"
            onClick={(event) => event.stopPropagation()}
          >
            <RoastCard card={detail} />
          </div>
        </div>
      )}
    </>
  );
}