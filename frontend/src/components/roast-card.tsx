import type { Card } from "@/lib/types";
import { relativeTime, sequence } from "@/lib/format";

const FALLBACK_QUOTE =
  "After careful consideration, we have decided to move forward with other candidates.";

/**
 * Roasts run from roughly 90 to 200 characters. A fixed size either wastes
 * space on the short ones or overflows on the long ones, so step it by length.
 */
function roastSize(text: string): string {
  if (text.length < 100) return "text-[1.6rem] leading-[1.18]";
  if (text.length < 150) return "text-[1.4rem] leading-[1.22]";
  return "text-[1.2rem] leading-[1.28]";
}

type Props = {
  card: Card;
  handle?: string;
  dragX?: number;
};

/**
 * The card visual. Pure, and deliberately unsized: it fills whatever container
 * it is given. The deck and the archive wrap it in a 4:5 box; the wall lets the
 * grid equalise heights. Imposing an aspect ratio here clipped the footer
 * whenever content ran taller than the ratio allowed.
 */
export function RoastCard({ card, handle = "@ishanpathak", dragX = 0 }: Props) {
  const hint = Math.min(Math.abs(dragX) / 90, 1);
  const publishing = dragX > 0;

  return (
    <div className="relative flex h-full min-h-[24rem] w-full flex-col overflow-hidden rounded-2xl bg-paper text-ink shadow-2xl shadow-black/50 ring-1 ring-black/20">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.045] [background-image:radial-gradient(#1a1a18_1px,transparent_1px)] [background-size:16px_16px]"
      />

      {dragX !== 0 && (
        <div
          aria-hidden
          className="pointer-events-none absolute right-5 top-16 z-20 rounded-sm border-2 border-stamp px-2.5 py-1 font-mono text-[0.6rem] font-semibold uppercase tracking-[0.2em] text-stamp"
          style={{
            opacity: hint,
            transform: `rotate(${publishing ? -9 : 9}deg)`,
          }}
        >
          {publishing ? "Publish" : "Filed"}
        </div>
      )}

      <header className="relative flex shrink-0 items-center gap-2.5 border-b border-rule px-5 pb-3.5 pt-4">
        <span aria-hidden className="size-2 shrink-0 rounded-full bg-stamp" />
        <p className="font-mono text-[0.6rem] font-semibold uppercase tracking-[0.24em] text-stamp">
          New rejection
        </p>
        <p className="ml-auto font-mono text-[0.6rem] uppercase tracking-[0.16em] text-ink-soft">
          {relativeTime(card.receivedAt)}
        </p>
      </header>

      <div className="relative flex flex-1 flex-col px-5 py-4">
        <h2 className="text-2xl font-bold leading-[0.95] tracking-tight text-balance">
          {card.company}
        </h2>
        <p className="mt-1.5 font-mono text-[0.6rem] uppercase tracking-[0.16em] text-ink-soft">
          Re: {card.role}
        </p>

        <p className="mt-4 line-clamp-2 text-[0.7rem] leading-relaxed text-ink-soft/80 line-through decoration-stamp decoration-2">
          &ldquo;{card.quote ?? FALLBACK_QUOTE}&rdquo;
        </p>

        <blockquote
          className={`my-auto py-4 font-semibold tracking-tight text-pretty ${roastSize(card.roast)}`}
        >
          {card.roast}
        </blockquote>
      </div>

      <footer className="relative flex shrink-0 items-center justify-between gap-3 border-t border-rule bg-ink/[0.03] px-5 py-3">
        <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-ink-soft">
          {sequence(card.seq)}
        </span>
        <span className="truncate font-mono text-[0.6rem] font-semibold uppercase tracking-[0.16em] text-ink/70">
          {handle}
        </span>
      </footer>
    </div>
  );
}