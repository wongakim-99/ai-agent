import { useState, type KeyboardEvent } from "react";

interface Props {
  loading: boolean;
  onSubmit: (question: string) => void;
}

const EXAMPLES = [
  "홍대에서 조용한 저녁 데이트 코스 짜줘, 카페 좋아해",
  "성수에서 전시 보고 저녁도 먹는 데이트",
  "강남에서 가볍게 커피 마시는 낮 데이트",
];

export function RequestBar({ loading, onSubmit }: Props) {
  const [value, setValue] = useState("");

  const submit = () => {
    const q = value.trim();
    if (q && !loading) onSubmit(q);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="rb">
      <div className="rb__row">
        <textarea
          className="rb__input"
          placeholder="어디서, 어떤 데이트를 하고 싶은지 자유롭게 적어보세요 (Enter 로 실행) — 예: 홍대에서 조용한 저녁 데이트"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKey}
          rows={2}
        />
        <button className="rb__btn" onClick={submit} disabled={loading || !value.trim()}>
          {loading ? "코스 짜는 중…" : "▶ 코스 추천"}
        </button>
      </div>
      <div className="rb__examples">
        {EXAMPLES.map((ex) => (
          <button key={ex} className="rb__chip" onClick={() => setValue(ex)} disabled={loading}>
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
