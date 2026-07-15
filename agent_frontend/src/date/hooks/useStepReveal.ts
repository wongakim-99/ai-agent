import { useCallback, useEffect, useRef, useState } from "react";
import type { DateStep } from "../types";

// step 은 노드가 끝나는 순간 통째로 도착한다 → 3~5번의 큰 점프로 툭툭 나타난다.
// 도착한 step 을 큐에 넣고 "제목 → 근거 한 줄씩" 순서로 풀어, 기다리는 동안 화면이 흐르게 한다.
// (lib/pacer.ts 와 같은 발상 — 백엔드는 데이터 그대로 흘리고 재생 속도는 순수 뷰 관심사)
// 연출이 LLM 대기 시간을 채우는 것이라, 대부분의 경우 체감 시간이 늘지 않는다.
const STEP_DELAY = 240; // 새 단계 제목이 뜨는 간격
const LINE_DELAY = 90; // 근거 한 줄이 붙는 간격

/** all 중 i번째 단계의 l번째 줄까지만 공개한 스냅샷 */
function snapshot(all: DateStep[], i: number, l: number): DateStep[] {
  const shown = all.slice(0, i);
  return i < all.length ? [...shown, { ...all[i], lines: all[i].lines.slice(0, l) }] : shown;
}

export interface StepReveal {
  steps: DateStep[]; // 지금까지 공개된 것 (마지막 단계는 줄이 채워지는 중일 수 있다)
  idle: boolean; // 큐가 비었다 = 도착한 걸 전부 보여줬다
  push: (step: DateStep) => void;
  reset: () => void;
}

export function useStepReveal(): StepReveal {
  const [steps, setSteps] = useState<DateStep[]>([]);
  const [idle, setIdle] = useState(true);
  const allRef = useRef<DateStep[]>([]); // 도착한 전체
  const posRef = useRef({ i: 0, l: 0 }); // 공개 커서: i번째 단계의 l번째 줄까지
  const timerRef = useRef<number>();

  // 커서를 한 칸 옮기고 다음 tick 을 예약한다. 큐를 다 따라잡으면 멈춘다.
  const tick = useCallback(() => {
    timerRef.current = undefined;
    const all = allRef.current;
    const pos = posRef.current;

    if (pos.i >= all.length) {
      setIdle(true);
      return;
    }

    let delay = LINE_DELAY;
    if (pos.l < all[pos.i].lines.length) {
      pos.l += 1; // 근거 한 줄 추가
    } else {
      pos.i += 1; // 다음 단계로
      pos.l = 0;
      delay = STEP_DELAY;
    }

    setSteps(snapshot(all, pos.i, pos.l));
    if (pos.i < all.length) timerRef.current = window.setTimeout(tick, delay);
    else setIdle(true);
  }, []);

  const push = useCallback(
    (step: DateStep) => {
      allRef.current = [...allRef.current, step];
      setIdle(false);
      // 첫 도착이면 제목을 바로 띄우고(대기 중 빈 화면 방지), 이후는 tick 이 알아서 따라잡는다.
      if (timerRef.current === undefined) {
        setSteps(snapshot(allRef.current, posRef.current.i, posRef.current.l));
        timerRef.current = window.setTimeout(tick, LINE_DELAY);
      }
    },
    [tick],
  );

  const reset = useCallback(() => {
    if (timerRef.current !== undefined) window.clearTimeout(timerRef.current);
    timerRef.current = undefined;
    allRef.current = [];
    posRef.current = { i: 0, l: 0 };
    setSteps([]);
    setIdle(true);
  }, []);

  // 언마운트 시 타이머 정리 (setState-after-unmount 방지)
  useEffect(() => () => {
    if (timerRef.current !== undefined) window.clearTimeout(timerRef.current);
  }, []);

  return { steps, idle, push, reset };
}
