// 이벤트 페이싱: SSE 는 규칙 기반 그래프에서 ms 단위로 끝나 애니메이션이 순식간에
// 지나간다. 수신 이벤트를 큐에 넣고 타입별 최소 간격으로 재생해 "눈으로 따라갈 수 있게" 한다.
// (백엔드는 데이터 그대로 흘리고, 재생 속도는 순수 뷰 관심사로 여기서만 다룬다)
import type { RunEvent } from "../types";

// 이벤트 타입별 기본 재생 간격(ms). node_start/edge_taken 이 핵심 시각 이벤트라 길게.
const BASE_DELAY: Record<string, number> = {
  run_start: 120,
  node_start: 500,
  edge_taken: 500,
  node_end: 350,
  state: 0,
  token: 15,
  done: 120,
  error: 120,
};

export interface Pacer {
  push(ev: RunEvent): void;
  flush(): void; // 남은 이벤트 즉시 전부 dispatch (끝까지 건너뛰기)
  clear(): void; // 타이머+큐 폐기 (중지/그래프 전환)
  setSpeed(mult: number): void; // 0 = 즉시, 0.5/1/2 = 배속
}

export function createPacer(dispatch: (ev: RunEvent) => void): Pacer {
  let queue: RunEvent[] = [];
  let timer: number | undefined;
  let speed = 1; // 0 이면 즉시 모드
  let draining = false;

  function delayFor(ev: RunEvent): number {
    if (speed === 0) return 0;
    return (BASE_DELAY[ev.type] ?? 120) / speed;
  }

  function schedule() {
    if (draining || timer !== undefined || queue.length === 0) return;
    const head = queue[0];
    timer = window.setTimeout(() => {
      timer = undefined;
      const ev = queue.shift();
      if (!ev) return;
      if (ev.type === "token") {
        // 같은 노드의 연속 토큰은 한 틱에 최대 5개까지 합쳐 dispatch(홍수 방지)
        let text = ev.text;
        let merged = 0;
        while (merged < 4 && queue.length && queue[0].type === "token" && queue[0].node === ev.node) {
          const next = queue.shift() as Extract<RunEvent, { type: "token" }>;
          text += next.text;
          merged++;
        }
        dispatch({ ...ev, text });
      } else {
        dispatch(ev);
      }
      schedule();
    }, delayFor(head));
  }

  return {
    push(ev) {
      queue.push(ev);
      schedule();
    },
    flush() {
      if (timer !== undefined) {
        window.clearTimeout(timer);
        timer = undefined;
      }
      draining = true;
      const rest = queue;
      queue = [];
      for (const ev of rest) dispatch(ev);
      draining = false;
    },
    clear() {
      if (timer !== undefined) {
        window.clearTimeout(timer);
        timer = undefined;
      }
      queue = [];
    },
    setSpeed(mult) {
      speed = mult;
    },
  };
}
