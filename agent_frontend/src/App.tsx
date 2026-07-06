import { useEffect, useMemo, useState } from "react";

import { ChapterSelector } from "./components/ChapterSelector";
import { GraphCanvas } from "./components/GraphCanvas";
import { InputForm } from "./components/InputForm";
import { StatePanel } from "./components/StatePanel";
import { EventTimeline } from "./components/EventTimeline";
import { useGraphRun } from "./hooks/useGraphRun";
import { getTopology, listGraphs } from "./api/client";
import type { GraphSummary, Topology } from "./types";

export default function App() {
  const [graphs, setGraphs] = useState<GraphSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [topology, setTopology] = useState<Topology | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { runState, run, stop } = useGraphRun(topology);
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

  // 선택 바뀌면 토폴로지 로드 + 실행 중단
  useEffect(() => {
    if (!selectedId) return;
    stop();
    setTopology(null);
    getTopology(selectedId).then(setTopology).catch((e) => setLoadError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__title">
          <span className="app__logo">◈</span> LangGraph 토폴로지 실행 뷰어
          <span className="app__sub">챕터 2 · 3 · 배운 그래프를 눈으로</span>
        </div>
        <ChapterSelector graphs={graphs} selectedId={selectedId} onSelect={setSelectedId} />
      </header>

      {loadError && <div className="app__error">백엔드 연결 실패: {loadError} — uvicorn이 8000에 떠 있나요?</div>}

      {spec && (
        <div className="app__concept">
          <span className="app__concept-title">{spec.title}</span>
          <span className="app__concept-body">{spec.concept}</span>
        </div>
      )}

      <main className="app__main">
        <section className="app__canvas">
          {topology ? (
            <GraphCanvas topology={topology} runState={runState} />
          ) : (
            <div className="app__loading">토폴로지 불러오는 중…</div>
          )}
        </section>

        <aside className="app__side">
          {spec && (
            <InputForm
              spec={spec}
              running={runState.running}
              onRun={(input) => run(spec.id, input)}
              onStop={stop}
            />
          )}
          <StatePanel runState={runState} />
          <EventTimeline runState={runState} />
        </aside>
      </main>
    </div>
  );
}
