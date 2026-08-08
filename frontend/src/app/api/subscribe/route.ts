import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

/** Store a push subscription. Upserts, since browsers can re-issue the same
 *  endpoint and re-subscribing should not error. */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = await request.json();
  const { endpoint, keys } = body ?? {};

  if (!endpoint || !keys?.p256dh || !keys?.auth) {
    return NextResponse.json(
      { error: "endpoint and keys required" },
      { status: 400 },
    );
  }

  const { error } = await supabase
    .from("push_subscriptions")
    .upsert({ endpoint, p256dh: keys.p256dh, auth: keys.auth });

  if (error) {
    console.error("subscribe failed", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}

/** Remove a subscription the browser has revoked or replaced. */
export async function DELETE(request: NextRequest): Promise<NextResponse> {
  const { endpoint } = await request.json();

  if (!endpoint) {
    return NextResponse.json({ error: "endpoint required" }, { status: 400 });
  }

  await supabase.from("push_subscriptions").delete().eq("endpoint", endpoint);
  return NextResponse.json({ ok: true });
}