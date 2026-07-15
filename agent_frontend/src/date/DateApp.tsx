import { useEffect, useRef, useState } from "react";

import { ThemeToggle } from "../components/ThemeToggle";
import { useTheme } from "../hooks/useTheme";
import { CourseMap } from "./components/CourseMap";
import { ChatPanel } from "./components/ChatPanel";
import { useStepReveal } from "./hooks/useStepReveal";
import { getDateConfig, planDateStream } from "./api/client";
import type { ChatMessage, DatePlanResult, MapPlace } from "./types";

export default function DateApp() {
  const { theme, toggle } = useTheme();
  const [clientId, setClientId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [places, setPlaces] = useState<MapPlace[]>([]);
  // 실행 중 진행 상황. 도착한 step 을 한 줄씩 풀어 보여준다(끝나면 메시지의 result.steps 로 남는다).
  const reveal = useStepReveal();
  // 결과가 먼저 도착해도 진행 상황을 다 보여준 뒤에 답을 띄운다.
  const [pending, setPending] = useState<DatePlanResult | null>(null);
  const [typingId, setTypingId] = useState(0); // 이 id 의 답변만 타이핑 연출 (과거 메시지는 즉시)
  const idRef = useRef(0);

  // 네이버 지도 Client ID 를 백엔드에서 받아온다
  useEffect(() => {
    getDateConfig()
      .then((c) => setClientId(c.naverMapsClientId))
      .catch((e) => setError(String(e)));
  }, []);

  // 진행 상황을 다 푼 뒤(idle) 답변을 붙인다 → 과정 → 답 순서가 끊기지 않는다.
  useEffect(() => {
    if (!pending || !reveal.idle) return;
    const id = (idRef.current += 1);
    setMessages((prev) => [...prev, { id, role: "assistant", result: pending }]);
    setPlaces(pending.places); // 지도는 가장 최근 추천의 장소로 갱신
    setTypingId(id);
    setPending(null);
    setLoading(false);
    reveal.reset();
  }, [pending, reveal.idle, reveal.reset]);

  const onSend = (text: string) => {
    setMessages((prev) => [...prev, { id: (idRef.current += 1), role: "user", text }]);
    setLoading(true);
    setError(null);
    reveal.reset();
    planDateStream(text, (e) => {
      if (e.type === "step") reveal.push(e.step);
    })
      .then(setPending) // 표시는 위 effect 가 (진행 상황을 다 푼 뒤에) 맡는다
      .catch((e) => {
        setError(String(e));
        setLoading(false);
        reveal.reset();
      });
  };

  return (
    <div className="date">
      <header className="date__header">
        <div className="date__title">
          POI 추천 파이프라인
          <span className="date__sub">LangGraph 멀티에이전트 · 내부 테스트 콘솔</span>
        </div>
        <div className="header-actions">
          <a className="nav-link" href="/index.html">◈ 토폴로지 뷰어 →</a>
          <ThemeToggle theme={theme} onToggle={toggle} />
        </div>
      </header>

      {error && <div className="app__error">{error}</div>}

      <div className="date__body">
        <section className="date__map">
          <CourseMap clientId={clientId} places={places} />
        </section>
        <section className="date__chat">
          <ChatPanel
            messages={messages}
            loading={loading}
            liveSteps={reveal.steps}
            typingId={typingId}
            onSend={onSend}
          />
        </section>
      </div>
    </div>
  );
}
