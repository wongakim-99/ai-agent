import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { AgentSteps } from "./AgentSteps";
import { CourseList } from "./CourseList";
import type { ChatMessage, DateStep } from "../types";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  /** 실행 중인 요청의 진행 상황 (완료되면 마지막 메시지의 result.steps 로 넘어간다) */
  liveSteps: DateStep[];
  onSend: (text: string) => void;
}

// 샘플 질의 — planner 가 지역/카테고리를 뽑을 수 있게 '지역 + 조건' 형태를 유지한다.
const EXAMPLES = [
  "홍대 저녁 식사 · 조용한 카페 동선",
  "성수 전시 관람 후 식사 동선",
  "강남 카페 중심 오후 동선",
];

export function ChatPanel({ messages, loading, liveSteps, onSend }: Props) {
  const [value, setValue] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  // 새 메시지/진행 상황이 붙을 때마다 맨 아래로 스크롤
  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading, liveSteps]);

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
            <div className="chat__welcome-title">질의를 입력해 파이프라인을 실행하세요</div>
            <div className="chat__welcome-sub">
              지역과 조건을 자연어로 넣으면 노드별 실행 근거와 추천 결과를 보여줍니다.
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
                <AgentSteps steps={m.result.steps} />
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
            <div className="msg__bubble msg__bubble--ai">
              <AgentSteps steps={liveSteps} running />
            </div>
          </div>
        )}
      </div>

      <div className="chat__input">
        <textarea
          className="chat__textarea"
          placeholder="예: 홍대 저녁 식사 · 카페 동선 (Enter 실행)"
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
