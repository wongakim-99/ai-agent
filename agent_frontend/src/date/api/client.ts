import type { DateConfig, DatePlanResult } from "../types";

// 기존 src/api/client.ts 와 동일한 규약: !res.ok 면 throw, 호출부에서 배너로 표시.

export async function getDateConfig(): Promise<DateConfig> {
  const res = await fetch("/api/date/config");
  if (!res.ok) throw new Error(`GET /api/date/config 실패: ${res.status}`);
  return res.json();
}

export async function planDate(question: string): Promise<DatePlanResult> {
  const res = await fetch("/api/date/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`POST /api/date/plan 실패: ${res.status}`);
  return res.json();
}
