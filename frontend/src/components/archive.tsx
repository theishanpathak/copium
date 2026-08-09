"use client";

import { relativeTime, sequence } from "@/lib/format";
import type { Card } from "@/lib/types";

type Props = {
  cards: Card[];
  onTogglePublish: (card: Card) => void;
  onClose: () => void;
};

/**
 * Every card as a readable list. The roast is the thing being judged, so it
 * gets the space; company and date are supporting detail. Published rows carry
 * a coloured rule so the state of the whole list is scannable without reading
 * each button.
 */
export function Archive({ cards, onTogglePublish, onClose }: Props) {
  const publishedCount = cards.filter((card) => card.published).length;

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto bg-desk px-5 pb-20 pt-6">
      <div className="mx-auto flex max-w-xl items-baseline justify-between pb-5 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-desk-dim">
        <span>
          {cards.length} filed · {publishedCount} on the wall
        </span>
        <button onClick={onClose}>Close</button>
      </div>

      {cards.length === 0 ? (
        <p className="py-24 text-center font-mono text-[0.62rem] uppercase tracking-[0.18em] text-desk-dim">
          Nothing yet
        </p>
      ) : (
        <ul className="mx-auto max-w-xl">
          {cards.map((card) => (
            <li
              key={card.id}
              className={`border-l-2 py-5 pl-4 ${
                card.published ? "border-stamp" : "border-white/10"
              }`}
            >
              <p className="text-[0.95rem] leading-relaxed text-paper text-pretty">
                {card.roast}
              </p>

              <div className="mt-3 flex items-center justify-between gap-4">
                <p className="min-w-0 truncate font-mono text-[0.55rem] uppercase tracking-[0.16em] text-desk-dim">
                  {card.company} · {sequence(card.seq)}
                  {card.receivedAt && ` · ${relativeTime(card.receivedAt)}`}
                </p>

                <button
                  onClick={() => onTogglePublish(card)}
                  className={`shrink-0 rounded-full border px-3 py-1.5 font-mono text-[0.55rem] uppercase tracking-[0.16em] transition-colors ${
                    card.published
                      ? "border-stamp text-stamp"
                      : "border-white/20 text-desk-dim hover:border-white/40 hover:text-paper"
                  }`}
                >
                  {card.published ? "On the wall" : "Publish"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}