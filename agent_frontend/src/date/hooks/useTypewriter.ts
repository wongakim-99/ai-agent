import { useEffect, useRef, useState } from "react";

// 요약문을 한 글자씩 찍어 "쓰는 중" 처럼 보이게 한다.
// 여기서 흐르는 건 이미 도착한 텍스트다 (모델이 실시간으로 뱉는 토큰이 아니라 연출).
// 진짜 토큰 스트리밍을 하려면 curator 를 '선정(구조화) → 해설(생성)' 2콜로 쪼개야 한다.
/** 한 글자당 ms. 요약 뒤에 코스를 이어 띄우는 쪽(CourseList)도 이 값으로 지연을 계산한다. */
export const CHAR_MS = 14;

/** 연출을 꺼달라고 한 사용자에게는 타이핑도 하지 않는다 (CSS 쪽 stagger 와 같은 규칙) */
const reducedMotion = () =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** enabled 면 text 를 한 글자씩 늘려 반환한다. 끄면 즉시 전체. */
export function useTypewriter(text: string, enabled: boolean) {
  const [shown, setShown] = useState(enabled ? "" : text);
  const timerRef = useRef<number>();

  useEffect(() => {
    if (!enabled || reducedMotion()) {
      setShown(text);
      return;
    }
    let n = 0;
    const step = () => {
      n += 1;
      setShown(text.slice(0, n));
      if (n < text.length) timerRef.current = window.setTimeout(step, CHAR_MS);
    };
    setShown("");
    timerRef.current = window.setTimeout(step, CHAR_MS);
    return () => {
      if (timerRef.current !== undefined) window.clearTimeout(timerRef.current);
    };
  }, [text, enabled]);

  return { shown, typing: enabled && shown.length < text.length };
}
