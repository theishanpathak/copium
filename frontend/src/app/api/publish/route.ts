import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

/** Toggle whether a card appears on the public wall.
 *
 * Separate from /api/viewed because that route also stamps viewed_at, and
 * changing your mind about publishing should not rewrite when you first saw
 * the card.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const { id, published } = await request.json();

  if (!id || typeof published !== "boolean") {
    return NextResponse.json(
      { error: "id and published required" },
      { status: 400 },
    );
  }

  const { error } = await supabase
    .from("rejections")
    .update({ published })
    .eq("id", id);

  if (error) {
    console.error("publish toggle failed", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}