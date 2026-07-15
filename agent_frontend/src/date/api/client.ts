import { parseSse } from "../../api/sse";
import type { DateConfig, DatePlanResult, DateRunEvent } from "../types";

// 기존 src/api/client.ts 와 동일한 규약: !res.ok 면 throw, 호출부에서 배너로 표시.

export async function getDateConfig(): Promise<DateConfig> {
  const res = await fetch("/api/date/config");
  if (!res.ok) throw new Error(`GET /api/date/config 실패: ${res.status}`);
  return res.json();
}

/** 코스를 짜면서 진행 상황(step)을 흘려보내고, 끝나면 최종 결과를 resolve 한다. */
export async function planDateStream(
  question: string,
  onEvent: (e: DateRunEvent) => void,
): Promise<DatePlanResult> {
  const res = await fetch("/api/date/plan/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok || !res.body) throw new Error(`POST /api/date/plan/stream 실패: ${res.status}`);

  // 그래프 실행 중 에러는 HTTP 상태가 아니라 error 이벤트로 온다 (헤더는 이미 나간 뒤라서).
  let result: DatePlanResult | null = null;
  let failure = "";
  await parseSse<DateRunEvent>(res.body, (e) => {
    onEvent(e);
    if (e.type === "done") result = e.result;
    if (e.type === "error") failure = e.message;
  });

  if (failure) throw new Error(failure);
  if (!result) throw new Error("스트림이 done 없이 끊겼습니다");
  return result;
}
