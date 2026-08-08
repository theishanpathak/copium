"use client";

import { useRef, useState } from "react";
import { RoastCard } from "@/components/roast-card";
import type { Card } from "@/lib/types";

const THRESHOLD = 100;
const VISIBLE = 3;
/** Mount one extra so the incoming card is already in the DOM before it shows. */
const RENDERED = VISIBLE + 1;
const LEAVE_MS = 300;

type Props = {
  cards: Card[];
  onFile: (card: Card, published: boolean) => void;
};

/** Owns the swipe interaction. Rendering is delegated to RoastCard. */
export function RoastStack({ cards, onFile }: Props) {
  const [top, setTop] = useState(0);
  const [dragX, setDragX] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const startX = useRef<number | null>(null);

  const card = cards[top];
  const done = top >= cards.length;

  function advance(direction: number) {
    setLeaving(true);
    setDragX(direction * window.innerWidth);
    onFile(card, direction > 0);

    window.setTimeout(() => {
      setTop((t) => t + 1);
      setDragX(0);
      setLeaving(false);
    }, LEAVE_MS);
  }

  function onPointerDown(event: React.PointerEvent) {
    if (leaving || done) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    startX.current = event.clientX;
    setDragging(true);
  }

  function onPointerMove(event: React.PointerEvent) {
    if (startX.current === null) return;
    setDragX(event.clientX - startX.current);
  }

  function onPointerUp() {
    if (startX.current === null) return;
    startX.current = null;
    setDragging(false);

    if (Math.abs(dragX) > THRESHOLD) advance(Math.sign(dragX));
    else setDragX(0);
  }

  if (done) {
    return (
      <div className="flex aspect-4/5 w-full flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-white/15 px-8 text-center">
        <p className="text-xl font-semibold">Inbox zero.</p>
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-desk-dim">
          Go get the next one
        </p>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      <div className="flex justify-center gap-1.5 pb-5" aria-hidden>
        {cards.map((_, i) => (
          <span
            key={i}
            className={`h-1 rounded-full transition-all duration-300 ${
              i < top
                ? "w-3 bg-stamp/40"
                : i === top
                  ? "w-7 bg-stamp"
                  : "w-3 bg-white/15"
            }`}
          />
        ))}
      </div>

      <div className="relative aspect-4/5 w-full">
        {cards
          .slice(top, top + RENDERED)
          .map((entry, depth) => ({ entry, depth }))
          .reverse()
          .map(({ entry, depth }) => {
            const isTop = depth === 0;

            // While the top card flies away, promote everything behind it
            // immediately. By the time `top` increments the next card is
            // already at the front, so the swap itself is invisible. Without
            // this the promotion animation runs *after* the swipe finishes and
            // reads as lag.
            const rank = leaving ? depth - 1 : depth;

            // No transition while a finger is down, or the card eases toward
            // the pointer instead of tracking it.
            const animated = !(isTop && dragging);

            return (
              <div
                key={entry.id}
                className={`absolute inset-0 touch-none select-none ${
                  isTop
                    ? "cursor-grab active:cursor-grabbing"
                    : "pointer-events-none"
                } ${animated ? "transition-[transform,opacity] duration-300 ease-out" : ""}`}
                style={{
                  transform: isTop
                    ? `translateX(${dragX}px) rotate(${dragX / 24}deg)`
                    : `translateY(${rank * 12}px) scale(${1 - rank * 0.04})`,
                  opacity: isTop
                    ? leaving
                      ? 0
                      : 1
                    : rank >= VISIBLE
                      ? 0
                      : 1 - rank * 0.22,
                  zIndex: VISIBLE - rank,
                }}
                onPointerDown={isTop ? onPointerDown : undefined}
                onPointerMove={isTop ? onPointerMove : undefined}
                onPointerUp={isTop ? onPointerUp : undefined}
                onPointerCancel={isTop ? onPointerUp : undefined}
              >
                <RoastCard card={entry} dragX={isTop ? dragX : 0} />
              </div>
            );
          })}
      </div>
    </div>
  );
}