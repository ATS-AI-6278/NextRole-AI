"use client";

import { useEffect, useMemo, useState } from "react";

import { getApplications, type JobApplication } from "../../src/lib/api";

export default function DashboardPage() {
  const [chatId, setChatId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [apps, setApps] = useState<JobApplication[]>([]);
  const backendBase = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "", []);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("telegram_chat_id");
      if (saved) setChatId(saved);
    } catch {
      // ignore
    }
  }, []);

  async function refresh() {
    const trimmed = chatId.trim();
    if (!trimmed) return;
    setLoading(true);
    try {
      const data = await getApplications(trimmed);
      setApps(data);
    } catch (e: any) {
      setApps([]);
      alert(e?.message || "Failed to load applications");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 10 }}>Job Application Dashboard</h1>

      <div style={{ marginBottom: 12 }}>
        <label style={{ display: "block", marginBottom: 8 }}>
          Telegram chat_id
          <input
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
            style={{ display: "block", width: "100%", maxWidth: 520, padding: 10, marginTop: 8 }}
            placeholder="e.g. 123456789"
          />
        </label>

        <div style={{ display: "flex", gap: 10, marginTop: 8, alignItems: "center" }}>
          <button
            onClick={refresh}
            disabled={loading || !chatId.trim()}
            style={{ padding: "10px 14px", cursor: loading ? "progress" : "pointer" }}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
          <span style={{ fontSize: 12, color: "#555" }}>
            Backend: {backendBase || "(set NEXT_PUBLIC_BACKEND_URL)"}
          </span>
        </div>
      </div>

      {apps.length === 0 ? (
        <p>No applications found yet.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", paddingBottom: 8 }}>Company</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", paddingBottom: 8 }}>Role</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", paddingBottom: 8 }}>Status</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", paddingBottom: 8 }}>Applied</th>
            </tr>
          </thead>
          <tbody>
            {apps.map((j) => (
              <tr key={j.id}>
                <td style={{ paddingTop: 12 }}>{j.company}</td>
                <td style={{ paddingTop: 12 }}>{j.role || "-"}</td>
                <td style={{ paddingTop: 12 }}>{j.status}</td>
                <td style={{ paddingTop: 12 }}>{j.applied_at || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}

