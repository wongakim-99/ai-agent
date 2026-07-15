import { useEffect, useRef, useState } from "react";

import { ThemeToggle } from "../components/ThemeToggle";
import { useTheme } from "../hooks/useTheme";
import { CourseMap } from "./components/CourseMap";
import { ChatPanel } from "./components/ChatPanel";
import { getDateConfig, planDateStream } from "./api/client";
import type { ChatMessage, DateStep, MapPlace } from "./types";

export default function DateApp() {
  const { theme, toggle } = useTheme();
  const [clientId, setClientId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [places, setPlaces] = useState<MapPlace[]>([]);
  // 실행 중에만 쓰는 진행 상황. 끝나면 결과(result.steps)로 옮겨가 메시지에 남는다.
  const [liveSteps, setLiveSteps] = useState<DateStep[]>([]);
  const idRef = useRef(0);

  // 네이버 지도 Client ID 를 백엔드에서 받아온다
  useEffect(() => {
    getDateConfig()
      .then((c) => setClientId(c.naverMapsClientId))
      .catch((e) => setError(String(e)));
  }, []);

  const onSend = (text: string) => {
    setMessages((prev) => [...prev, { id: (idRef.current += 1), role: "user", text }]);
    setLoading(true);
    setError(null);
    setLiveSteps([]);
    planDateStream(text, (e) => {
      if (e.type === "step") setLiveSteps((prev) => [...prev, e.step]);
    })
      .then((result) => {
        setMessages((prev) => [...prev, { id: (idRef.current += 1), role: "assistant", result }]);
        setPlaces(result.places); // 지도는 가장 최근 추천의 장소로 갱신
      })
      .catch((e) => setError(String(e)))
      .finally(() => {
        setLoading(false);
        setLiveSteps([]); // 완료된 과정은 방금 추가된 메시지가 result.steps 로 들고 있다
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
          <ChatPanel messages={messages} loading={loading} liveSteps={liveSteps} onSend={onSend} />
        </section>
      </div>
    </div>
  );
}
