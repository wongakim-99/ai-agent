import type { RunState } from "../hooks/useGraphRun";

interface Props {
  runState: RunState;
}

function render(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

// 실행되며 채워지는 State/출력을 key-value 로 보여준다.
// 가장 최근 node_end 가 바꾼 키는 잠깐 강조(changedKeys)한다.
export function StatePanel({ runState }: Props) {
  const entries = Object.entries(runState.state);

  return (
    <div className="panel">
      <div className="panel__title">State</div>
      {entries.length === 0 && <div className="panel__empty">실행하면 State가 여기에 채워집니다.</div>}
      <div className="statelist">
        {entries.map(([k, v]) => {
          const empty = v === "" || v === null || (Array.isArray(v) && v.length === 0);
          const changed = runState.changedKeys.has(k);
          return (
            <div
              key={k}
              className={`stateitem ${empty ? "stateitem--empty" : "stateitem--filled"} ${
                changed ? "stateitem--changed" : ""
              }`}
            >
              <span className="stateitem__key">{k}</span>
              <pre className="stateitem__val">{render(v)}</pre>
            </div>
          );
        })}
      </div>
    </div>
  );
}
