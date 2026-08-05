import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const payload = await request.json();
  console.log("yo, just got a new email!", JSON.stringify(payload));
  
  // Pub/Sub wraps the actual Gmail notification in a base64-encoded "message.data" field
  const decoded = Buffer.from(payload.message.data, "base64").toString("utf-8")
  const gmailNotification = JSON.parse(decoded)       // { emailAddress, historyId }

  await fetch(
    `https://api.github.com/repos/${process.env.GITHUB_REPO}/dispatches`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
      },
      body: JSON.stringify({
        event_type: "gmail_notification",
        client_payload: { historyId: gmailNotification.historyId },
      }),
    }
  );

  return NextResponse.json({ received: true });
}