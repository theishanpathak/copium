import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const { GITHUB_REPO, GITHUB_TOKEN, WEBHOOK_SECRET } = process.env;

  // The repo is public, so this URL is discoverable. Without a shared secret,
  // anyone could trigger pipeline runs and burn OpenAI/Tavily credits.
  if (WEBHOOK_SECRET) {
    const provided = request.nextUrl.searchParams.get("secret");
    if (provided !== WEBHOOK_SECRET) {
      console.error("webhook: bad or missing secret");
      return NextResponse.json({ error: "unauthorized" }, { status: 401 });
    }
  }

  if (!GITHUB_REPO || !GITHUB_TOKEN) {
    console.error("webhook: GITHUB_REPO or GITHUB_TOKEN not set");
    return NextResponse.json({ received: true });
  }

  let historyId: string | undefined;

  try {
    const payload = await request.json();
    // Pub/Sub wraps the Gmail notification in a base64 "message.data" field.
    // Test messages and empty publishes can arrive without it.
    const data = payload?.message?.data;
    if (!data) {
      console.log("webhook: no message.data, ignoring");
      return NextResponse.json({ received: true });
    }

    const decoded = Buffer.from(data, "base64").toString("utf-8");
    historyId = JSON.parse(decoded).historyId; // { emailAddress, historyId }
  } catch (err) {
    console.error("webhook: could not parse payload", err);
    return NextResponse.json({ received: true });
  }

  const res = await fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        event_type: "gmail_notification",
        client_payload: { historyId },
      }),
    },
  );

  if (res.ok) {
    console.log(`webhook: dispatched, historyId=${historyId}`);
    return NextResponse.json({ received: true });
  }

  const body = await res.text();
  console.error(`webhook: dispatch failed ${res.status} ${body}`);

  // 4xx means the token or repo is wrong and retrying will never help, so ack
  // to stop Pub/Sub redelivering for days. 5xx is transient, so let it retry.
  const status = res.status >= 500 ? 502 : 200;
  return NextResponse.json({ received: res.status < 500 }, { status });
}