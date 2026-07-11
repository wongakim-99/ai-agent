interface Props {
  speed: number;
  onSpeed: (mult: number) => void;
  running: boolean;
  onSkip: () => void;
}

// 재생 속도(0.5×/1×/2×/즉시) + 실행 중 "끝까지" 건너뛰기.
// 규칙 기반 그래프는 순식간에 끝나므로, 기본 재생을 느리게 두고 원할 때 건너뛴다.
const OPTIONS: { label: string; mult: number }[] = [
  { label: "0.5×", mult: 0.5 },
  { label: "1×", mult: 1 },
  { label: "2×", mult: 2 },
  { label: "즉시", mult: 0 },
];

export function PlaybackControls({ speed, onSpeed, running, onSkip }: Props) {
  return (
    <div className="playback">
      <span className="playback__label">재생 속도</span>
      <div className="playback__seg">
        {OPTIONS.map((o) => (
          <button
            key={o.label}
            className={`playback__btn ${speed === o.mult ? "playback__btn--active" : ""}`}
            onClick={() => onSpeed(o.mult)}
          >
            {o.label}
          </button>
        ))}
      </div>
      {running && (
        <button className="playback__skip" onClick={onSkip} title="남은 애니메이션 건너뛰기">
          끝까지 ▸
        </button>
      )}
    </div>
  );
}
