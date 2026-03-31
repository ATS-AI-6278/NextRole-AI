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

