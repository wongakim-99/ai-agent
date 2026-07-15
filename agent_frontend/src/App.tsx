import { useEffect, useMemo, useState } from "react";

import { GraphSidebar } from "./components/GraphSidebar";
import { GraphCanvas } from "./components/GraphCanvas";
import { InputForm } from "./components/InputForm";
import { PlaybackControls } from "./components/PlaybackControls";
import { StatePanel } from "./components/StatePanel";
import { NarrationTimeline } from "./components/NarrationTimeline";
import { ThemeToggle } from "./components/ThemeToggle";
import { useGraphRun } from "./hooks/useGraphRun";
import { useTheme } from "./hooks/useTheme";
import { getTopology, listGraphs } from "./api/client";
import type { GraphSummary, Topology } from "./types";

export default function App() {
  const { theme, toggle } = useTheme();
  const [graphs, setGraphs] = useState<GraphSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { runState, run, stop, clear, speed, setSpeed, skip } = useGraphRun(topology);
  const spec = useMemo(() => graphs.find((g) => g.id === selectedId) ?? null, [graphs, selectedId]);

  // 목록 로드 → 기본 선택(3-1)
  useEffect(() => {
    listGraphs()
      .then((gs) => {
        setGraphs(gs);
        setSelectedId(gs.find((g) => g.id === "3-1")?.id ?? gs[0]?.id ?? null);
      })
      .catch((e) => setLoadError(String(e)));
  }, []);

  // 선택 바뀌면 토폴로지 로드 + 이전 실행 결과 초기화
  useEffect(() => {
    if (!selectedId) return;
    clear();
    setTopology(null);
    getTopology(selectedId).then(setTopology).catch((e) => setLoadError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__title">
          <span className="app__logo">◈</span> LangGraph 토폴로지 실행 뷰어
          <span className="app__sub">배운 그래프를 눈으로</span>
        </div>
        <div className="header-actions">
          <a className="nav-link" href="/date.html">POI 파이프라인 →</a>
          <ThemeToggle theme={theme} onToggle={toggle} />
        </div>
      </header>

      {loadError && (
        <div className="app__error">백엔드 연결 실패: {loadError} — uvicorn이 8000에 떠 있나요?</div>
      )}

      <div className="app__body">
        <GraphSidebar graphs={graphs} selectedId={selectedId} onSelect={setSelectedId} />

        <main className="app__canvas">
          {topology ? (
            <GraphCanvas topology={topology} runState={runState} colorMode={theme} />
          ) : (
            <div className="app__loading">토폴로지 불러오는 중…</div>
          )}
        </main>

        <aside className="app__side">
          {spec && (
            <>
              <InputForm
                spec={spec}
                running={runState.running}
                onRun={(input) => run(spec.id, input)}
                onStop={stop}
              />
              <PlaybackControls
                speed={speed}
                onSpeed={setSpeed}
                running={runState.running}
                onSkip={skip}
              />
            </>
          )}
          <StatePanel runState={runState} />
          <NarrationTimeline runState={runState} />
        </aside>
      </div>
    </div>
  );
}
