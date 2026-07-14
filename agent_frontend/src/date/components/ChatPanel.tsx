import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { CourseList } from "./CourseList";
import type { ChatMessage } from "../types";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
}

const EXAMPLES = [
  "홍대에서 조용한 저녁 데이트 코스 짜줘, 카페 좋아해",
  "성수에서 전시 보고 저녁도 먹는 데이트",
  "강남에서 가볍게 커피 마시는 낮 데이트",
];

export function ChatPanel({ messages, loading, onSend }: Props) {
  const [value, setValue] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  // 새 메시지/로딩 상태에서 맨 아래로 스크롤
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const submit = () => {
    const t = value.trim();
    if (t && !loading) {
      onSend(t);
      setValue("");
    }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat">
      <div className="chat__log" ref={logRef}>
        {messages.length === 0 && (
          <div className="chat__welcome">
            <div className="chat__welcome-title">어디로 데이트 갈까요? 💕</div>
            <div className="chat__welcome-sub">
              지역과 분위기를 말해주면 실제 장소로 코스를 짜드려요.
            </div>
            <div className="chat__examples">
              {EXAMPLES.map((ex) => (
                <button key={ex} className="chat__chip" onClick={() => onSend(ex)} disabled={loading}>
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="msg msg--user">
              <div className="msg__bubble msg__bubble--user">{m.text}</div>
            </div>
          ) : (
            <div key={m.id} className="msg msg--ai">
              <div className="msg__bubble msg__bubble--ai">
                <CourseList
                  region={m.result.region}
                  summary={m.result.summary}
                  course={m.result.course}
                />
              </div>
            </div>
          ),
        )}

        {loading && (
          <div className="msg msg--ai">
            <div className="msg__bubble msg__bubble--ai chat__typing">코스 짜는 중…</div>
          </div>
        )}
      </div>

      <div className="chat__input">
        <textarea
          className="chat__textarea"
          placeholder="예: 홍대에서 조용한 저녁 데이트 (Enter 전송)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKey}
          rows={1}
        />
        <button className="chat__send" onClick={submit} disabled={loading || !value.trim()}>
          ▶
        </button>
      </div>
    </div>
  );
}
