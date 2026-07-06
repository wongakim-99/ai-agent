import type { GraphSummary, Topology, RunEvent } from "../types";
import { parseSse } from "./sse";

export async function listGraphs(): Promise<GraphSummary[]> {
  const res = await fetch("/graphs");
  if (!res.ok) throw new Error(`GET /graphs 실패: ${res.status}`);
  return res.json();
}

export async function getTopology(id: string): Promise<Topology> {
  const res = await fetch(`/graphs/${id}/topology`);
  if (!res.ok) throw new Error(`GET /graphs/${id}/topology 실패: ${res.status}`);
  return res.json();
}

export async function runGraph(
  id: string,
  input: Record<string, unknown>,
  onEvent: (e: RunEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const res = await fetch(`/graphs/${id}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
    signal,
  });
  if (!res.ok) throw new Error(`POST /graphs/${id}/run 실패: ${res.status}`);
  if (!res.body) throw new Error("응답에 스트림 본문이 없습니다.");
  await parseSse<RunEvent>(res.body, onEvent);
}
