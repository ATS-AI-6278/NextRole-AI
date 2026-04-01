export type JobApplication = {
  id: number;
  company: string;
  role: string | null;
  applied_at: string | null;
  status: string;
  last_status_at: string | null;
};

const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL;

export async function getApplications(chatId: string): Promise<JobApplication[]> {
  if (!backendBase) throw new Error("NEXT_PUBLIC_BACKEND_URL is not set");

  const res = await fetch(`${backendBase}/dashboard/applications`, {
    method: "GET",
    headers: {
      "x-telegram-chat-id": chatId,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error ${res.status}: ${text}`);
  }
  return (await res.json()) as JobApplication[];
}

export type ScanStatus = {
  id: number;
  status: string;
  processed_count: number;
  scan_limit: number;
  updated_at: string | null;
};

export async function getScanStatus(chatId: string): Promise<ScanStatus> {
  const res = await fetch(`${backendBase}/dashboard/scan-status`, {
    headers: { "x-telegram-chat-id": chatId },
  });
  return (await res.json()) as ScanStatus;
}

export type JobStats = Record<string, number>;

export async function getStats(chatId: string): Promise<JobStats> {
  const res = await fetch(`${backendBase}/dashboard/stats`, {
    headers: { "x-telegram-chat-id": chatId },
  });
  return (await res.json()) as JobStats;
}

