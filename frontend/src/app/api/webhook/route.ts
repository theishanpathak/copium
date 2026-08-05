import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = await request.json();
  console.log("Webhook received:", body);
  return NextResponse.json({ received: true });
}