import { useEffect, useState } from "react";

import { ThemeToggle } from "../components/ThemeToggle";
import { useTheme } from "../hooks/useTheme";
import { RequestBar } from "./components/RequestBar";
import { CourseMap } from "./components/CourseMap";
import { CourseList } from "./components/CourseList";
import { getDateConfig, planDate } from "./api/client";
import type { DatePlanResult } from "./types";

export default function DateApp() {
  const { theme, toggle } = useTheme();
  const [kakaoJsKey, setKakaoJsKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DatePlanResult | null>(null);

  // 지도 SDK 용 JS 키를 백엔드에서 받아온다 (키 출처는 루트 .env 하나)
  useEffect(() => {
    getDateConfig()
      .then((c) => setKakaoJsKey(c.kakaoJsKey))
      .catch((e) => setError(String(e)));
  }, []);

  const onSubmit = (question: string) => {
    setLoading(true);
    setError(null);
    planDate(question)
      .then(setResult)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  return (
    <div className="date">
      <header className="date__header">
        <div className="date__title">
          <span className="date__logo">❤</span> 데이트 코스 플래너
          <span className="date__sub">AI가 실제 장소로 코스를 짜드려요</span>
        </div>
        <ThemeToggle theme={theme} onToggle={toggle} />
      </header>

      <RequestBar loading={loading} onSubmit={onSubmit} />

      {error && <div className="app__error">{error}</div>}

      <main className="date__body">
        {result ? (
          <>
            <section className="date__map">
              <CourseMap jsKey={kakaoJsKey} places={result.places} />
            </section>
            <section className="date__list">
              <CourseList region={result.region} summary={result.summary} course={result.course} />
            </section>
          </>
        ) : (
          <div className="date__placeholder">
            {loading
              ? "코스를 짜는 중이에요…"
              : "위에 요청을 입력하고 ▶ 코스 추천을 눌러보세요."}
          </div>
        )}
      </main>
    </div>
  );
}
