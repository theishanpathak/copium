import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE } from "@/lib/auth";

/** Paths reachable without the cookie. /api/webhook must stay open because
 *  Pub/Sub pushes cannot carry our session. */
const OPEN_PATHS = ["/login", "/api/login", "/wall", "/api/webhook"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (OPEN_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  const token = request.cookies.get(AUTH_COOKIE)?.value;
  if (token && token === process.env.AUTH_TOKEN) {
    return NextResponse.next();
  }

  // API routes get a status, not a redirect, so fetch() failures are legible.
  if (pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const login = request.nextUrl.clone();
  login.pathname = "/login";
  login.searchParams.set("next", pathname);
  return NextResponse.redirect(login);
}

export const config = {
  // Skip Next internals and any path with a file extension, so the manifest,
  // service worker, and icons stay reachable.
  matcher: ["/((?!_next/static|_next/image|.*\\.).*)"],
};