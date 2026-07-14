import { useEffect, useRef, useState } from "react";

import { ThemeToggle } from "../components/ThemeToggle";
import { useTheme } from "../hooks/useTheme";
import { CourseMap } from "./components/CourseMap";
import { ChatPanel } from "./components/ChatPanel";
import { getDateConfig, planDate } from "./api/client";
import type { ChatMessage, MapPlace } from "./types";

export default function DateApp() {
  const { theme, toggle } = useTheme();
  const [clientId, setClientId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [places, setPlaces] = useState<MapPlace[]>([]);
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
    planDate(text)
      .then((result) => {
        setMessages((prev) => [...prev, { id: (idRef.current += 1), role: "assistant", result }]);
        setPlaces(result.places); // 지도는 가장 최근 추천의 장소로 갱신
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  return (
    <div className="date">
      <header className="date__header">
        <div className="date__title">
          <span className="date__logo">❤</span> 데이트 코스 플래너
          <span className="date__sub">AI와 대화하며 실제 장소로 코스를 짜보세요</span>
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
          <ChatPanel messages={messages} loading={loading} onSend={onSend} />
        </section>
      </div>
    </div>
  );
}
