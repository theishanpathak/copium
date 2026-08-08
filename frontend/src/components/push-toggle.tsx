"use client";

import { useEffect, useState } from "react";

type State = "loading" | "unsupported" | "install" | "off" | "on" | "denied";

/** VAPID keys are base64url; the Push API wants raw bytes.
 *  Typed as Uint8Array<ArrayBuffer> because BufferSource rejects the
 *  SharedArrayBuffer-compatible default since TypeScript 5.7. */
function decodeKey(base64: string): Uint8Array<ArrayBuffer> {
  const padded = (base64 + "=".repeat((4 - (base64.length % 4)) % 4))
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));

  for (let i = 0; i < raw.length; i++) {
    bytes[i] = raw.charCodeAt(i);
  }

  return bytes;
}

export function PushToggle() {
  const [state, setState] = useState<State>("loading");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    async function detect() {
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        // iOS Safari only exposes PushManager once installed to the home
        // screen, so this branch is also the "not installed yet" case.
        const iOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
        setState(iOS ? "install" : "unsupported");
        return;
      }

      if (Notification.permission === "denied") {
        setState("denied");
        return;
      }

      const registration = await navigator.serviceWorker.getRegistration();
      const existing = await registration?.pushManager.getSubscription();
      setState(existing ? "on" : "off");
    }

    detect().catch(() => setState("unsupported"));
  }, []);

  async function enable() {
    setBusy(true);

    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setState(permission === "denied" ? "denied" : "off");
        return;
      }

      const registration = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: decodeKey(
          process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY!,
        ),
      });

      const response = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(subscription.toJSON()),
      });

      if (!response.ok) throw new Error(await response.text());
      setState("on");
    } catch (error) {
      console.error("push subscribe failed", error);
      setState("off");
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setBusy(true);

    try {
      const registration = await navigator.serviceWorker.getRegistration();
      const subscription = await registration?.pushManager.getSubscription();

      if (subscription) {
        await fetch("/api/subscribe", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: subscription.endpoint }),
        });
        await subscription.unsubscribe();
      }

      setState("off");
    } catch (error) {
      console.error("push unsubscribe failed", error);
    } finally {
      setBusy(false);
    }
  }

  if (state === "loading" || state === "unsupported") return null;

  const label = {
    install: "Add to home screen for alerts",
    denied: "Notifications blocked",
    off: "Turn on alerts",
    on: "Alerts on",
  }[state];

  const inert = state === "install" || state === "denied";

  return (
    <button
      onClick={state === "on" ? disable : enable}
      disabled={busy || inert}
      className={`font-mono text-[0.58rem] uppercase tracking-[0.2em] ${
        state === "on" ? "text-stamp" : "text-desk-dim"
      } disabled:opacity-60`}
    >
      {busy ? "…" : label}
    </button>
  );
}