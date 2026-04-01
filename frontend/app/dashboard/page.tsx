"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { getApplications, getScanStatus, getStats, type JobApplication, type ScanStatus, type JobStats } from "../../src/lib/api";

export default function DashboardPage() {
  const [chatId, setChatId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [apps, setApps] = useState<JobApplication[]>([]);
  const [scan, setScan] = useState<ScanStatus | null>(null);
  const [stats, setStats] = useState<JobStats>({});
  
  const backendBase = useMemo(() => process.env.NEXT_PUBLIC_BACKEND_URL || "", []);

  const refresh = useCallback(async () => {
    const trimmed = chatId.trim();
    if (!trimmed) return;
    setLoading(true);
    try {
      const [appData, scanData, statsData] = await Promise.all([
        getApplications(trimmed),
        getScanStatus(trimmed),
        getStats(trimmed),
      ]);
      setApps(appData);
      setScan(scanData);
      setStats(statsData);
      localStorage.setItem("telegram_chat_id", trimmed);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [chatId]);

  useEffect(() => {
    const saved = localStorage.getItem("telegram_chat_id");
    if (saved) {
      setChatId(saved);
    }
  }, []);

  // Poll for scan status if running
  useEffect(() => {
    if (scan?.status === "running") {
      const timer = setInterval(refresh, 5000);
      return () => clearInterval(timer);
    }
  }, [scan?.status, refresh]);

  return (
    <main className="dashboard-container">
      <style jsx>{`
        .dashboard-container {
          min-height: 100vh;
          background: radial-gradient(circle at top left, #1a1a2e, #16213e);
          color: #fff;
          font-family: 'Inter', system-ui, -apple-system, sans-serif;
          padding: 40px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 40px;
        }
        .glass-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 16px;
          padding: 24px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
        }
        .stat-item {
          text-align: center;
        }
        .stat-value {
          font-size: 32px;
          font-weight: 700;
          color: #4cc9f0;
          margin-bottom: 4px;
        }
        .stat-label {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.6);
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .scan-status {
          margin-bottom: 40px;
        }
        .progress-bar-bg {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
          margin-top: 12px;
        }
        .progress-bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #4361ee, #4cc9f0);
          transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .table-container {
          overflow-x: auto;
        }
        table {
          width: 100%;
          border-spacing: 0;
        }
        th {
          text-align: left;
          padding: 16px;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          text-transform: uppercase;
        }
        td {
          padding: 16px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .status-badge {
          padding: 4px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
        }
        .status-applied { background: rgba(76, 201, 240, 0.2); color: #4cc9f0; }
        .status-interviewing { background: rgba(67, 97, 238, 0.2); color: #4361ee; }
        .status-offer { background: rgba(46, 196, 182, 0.2); color: #2ec4b6; }
        .status-rejected { background: rgba(230, 57, 70, 0.2); color: #e63946; }
        .input-group {
          display: flex;
          gap: 12px;
          margin-bottom: 30px;
        }
        input {
          flex: 1;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          padding: 12px 16px;
          color: #fff;
          outline: none;
        }
        input:focus { border-color: #4cc9f0; }
        button {
          background: #4cc9f0;
          color: #1a1a2e;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 700;
          cursor: pointer;
          transition: transform 0.2s;
        }
        button:hover:not(:disabled) { transform: translateY(-2px); }
        button:disabled { background: #555; cursor: not-allowed; }
      `}</style>

      <div className="header">
        <div>
          <h1 style={{ margin: 0, fontSize: 32 }}>NextRole AI</h1>
          <p style={{ color: "rgba(255,255,255,0.5)", marginTop: 4 }}>Career Command Center</p>
        </div>
        <div className="input-group">
          <input 
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
            placeholder="Telegram Chat ID"
          />
          <button onClick={refresh} disabled={loading}>{loading ? "Syncing..." : "Sync Now"}</button>
        </div>
      </div>

      <div className="stats-grid">
        {["Applied", "Interviewing", "Offer", "Rejected"].map(s => (
          <div key={s} className="glass-card stat-item">
            <div className="stat-value">{stats[s] || 0}</div>
            <div className="stat-label">{s}</div>
          </div>
        ))}
      </div>

      {scan && scan.status !== "none" && (
        <div className="glass-card scan-status">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{ fontSize: 18, fontWeight: 600 }}>
                {scan.status === "running" ? "🔍 Scan in Progress..." : "✅ Last Scan Complete"}
              </span>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", marginTop: 4 }}>
                Processed {scan.processed_count} / {scan.scan_limit} emails
              </div>
            </div>
            <div style={{ color: "#4cc9f0", fontWeight: 700 }}>
              {Math.round((scan.processed_count / scan.scan_limit) * 100)}%
            </div>
          </div>
          <div className="progress-bar-bg">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${(scan.processed_count / scan.scan_limit) * 100}%` }}
            />
          </div>
        </div>
      )}

      <div className="glass-card table-container">
        <h2 style={{ marginTop: 0, marginBottom: 20 }}>Recent Job Applications</h2>
        {apps.length === 0 ? (
          <p style={{ color: "rgba(255,255,255,0.4)" }}>No applications tracked yet. Use Telegram to start a scan!</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {apps.map(j => (
                <tr key={j.id}>
                  <td style={{ fontWeight: 600 }}>{j.company}</td>
                  <td style={{ color: "rgba(255,255,255,0.7)" }}>{j.role || "Specialist"}</td>
                  <td>
                    <span className={`status-badge status-${j.status.toLowerCase()}`}>
                      {j.status}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
                    {j.last_status_at ? new Date(j.last_status_at).toLocaleDateString() : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
