// ReadableStream(SSE) 파서: `data: {json}\n\n` 프레임을 잘라 콜백에 넘긴다.
// EventSource 는 GET 전용이라 POST 바디를 못 실어서 fetch + reader 로 직접 파싱한다.
export async function parseSse<T>(
  body: ReadableStream<Uint8Array>,
  onEvent: (e: T) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      try {
        onEvent(JSON.parse(line.slice(5).trim()) as T);
      } catch {
        // 부분 프레임/키프얼라이브 코멘트 등은 무시
      }
    }
  }
}
