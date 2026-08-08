"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();

  const [password, setPassword] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(false);

    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (response.ok) {
      router.replace(params.get("next") || "/");
      router.refresh();
    } else {
      setError(true);
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center px-6">
      <form onSubmit={submit} className="w-full max-w-xs">
        <p className="font-mono text-[0.62rem] uppercase tracking-[0.24em] text-stamp">
          Copium
        </p>

        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoFocus
          placeholder="Password"
          className="mt-5 w-full border-b border-white/20 bg-transparent pb-2 text-lg outline-none placeholder:text-desk-dim focus:border-stamp"
        />

        <button
          type="submit"
          disabled={busy || !password}
          className="mt-6 font-mono text-[0.62rem] uppercase tracking-[0.24em] text-desk-dim disabled:opacity-40"
        >
          {busy ? "…" : "Enter"}
        </button>

        {error && (
          <p className="mt-4 font-mono text-[0.62rem] uppercase tracking-[0.18em] text-stamp">
            Wrong password
          </p>
        )}
      </form>
    </main>
  );
}