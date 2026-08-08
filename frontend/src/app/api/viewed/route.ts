import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const { id, published } = await request.json();

  if (!id) {
    return NextResponse.json({ error: "id required" }, { status: 400 });
  }

  const { error } = await supabase
    .from("rejections")
    .update({
      viewed_at: new Date().toISOString(),
      published: published === true,
    })
    .eq("id", id);

  if (error) {
    console.error("mark viewed failed", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}