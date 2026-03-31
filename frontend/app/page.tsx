"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function HomePage() {
  const router = useRouter();
  const [chatId, setChatId] = useState("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("telegram_chat_id");
      if (saved) setChatId(saved);
    } catch {
      // ignore
    }
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 12 }}>NextRole AI Dashboard</h1>
      <p style={{ marginBottom: 18 }}>
        Set your Telegram <code>chat_id</code> so the dashboard can fetch your data.
      </p>

      <label style={{ display: "block", marginBottom: 8 }}>
        Telegram chat_id
        <input
          value={chatId}
          onChange={(e) => setChatId(e.target.value)}
          style={{ display: "block", width: "100%", maxWidth: 520, padding: 10, marginTop: 8 }}
          placeholder="e.g. 123456789"
        />
      </label>

      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => {
            try {
              localStorage.setItem("telegram_chat_id", chatId);
            } catch {
              // ignore
            }
            router.push("/dashboard");
          }}
          disabled={!chatId.trim()}
          style={{ padding: "10px 14px", cursor: chatId.trim() ? "pointer" : "not-allowed" }}
        >
          Continue
        </button>
      </div>
    </main>
  );
}

