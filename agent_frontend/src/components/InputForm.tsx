import { useEffect, useMemo, useState } from "react";

import type { GraphSummary } from "../types";

interface Props {
  spec: GraphSummary;
  running: boolean;
  onRun: (input: Record<string, unknown>) => void;
  onStop: () => void;
}

// input_example 에서 "편집 가능한" 필드(비어있지 않은 문자열)만 폼으로 노출한다.
// context/answer/notes 같은 초기 State 자리는 그대로 payload 에 실어 보낸다.
export function InputForm({ spec, running, onRun, onStop }: Props) {
  const editable = useMemo(
    () =>
      Object.entries(spec.input_example).filter(
        ([, v]) => typeof v === "string" && v.length > 0,
      ) as [string, string][],
    [spec],
  );

  const [values, setValues] = useState<Record<string, string>>({});

  // 패턴이 바뀌면 예시값으로 초기화
  useEffect(() => {
    setValues(Object.fromEntries(editable));
  }, [editable]);

  const submit = () => {
    const payload: Record<string, unknown> = { ...spec.input_example };
    for (const [k, v] of Object.entries(values)) payload[k] = v;
    onRun(payload);
  };

  return (
    <div className="inputform">
      {editable.map(([key]) => (
        <label key={key} className="inputform__field">
          <span className="inputform__key">{key}</span>
          <textarea
            className="inputform__textarea"
            rows={2}
            value={values[key] ?? ""}
            onChange={(e) => setValues((s) => ({ ...s, [key]: e.target.value }))}
          />
        </label>
      ))}
      <div className="inputform__actions">
        {running ? (
          <button className="btn btn--stop" onClick={onStop}>
            ■ 중지
          </button>
        ) : (
          <button className="btn btn--run" onClick={submit}>
            ▶ 실행
          </button>
        )}
      </div>
    </div>
  );
}
