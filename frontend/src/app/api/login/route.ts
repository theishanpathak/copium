import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE } from "@/lib/auth";

const YEAR = 60 * 60 * 24 * 365;

export async function POST(request: NextRequest): Promise<NextResponse> {
  const { password } = await request.json();

  if (!process.env.APP_PASSWORD || !process.env.AUTH_TOKEN) {
    console.error("login: APP_PASSWORD or AUTH_TOKEN not set");
    return NextResponse.json({ error: "not configured" }, { status: 500 });
  }

  if (password !== process.env.APP_PASSWORD) {
    return NextResponse.json({ error: "wrong password" }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });

  response.cookies.set(AUTH_COOKIE, process.env.AUTH_TOKEN, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    // Long-lived on purpose: the installed PWA should not ask again.
    maxAge: YEAR,
  });

  return response;
}