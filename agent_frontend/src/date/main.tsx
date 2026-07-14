import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import DateApp from "./DateApp";
import "../styles/app.css"; // 테마 변수 + 기본 리셋 (토폴로지 앱과 공유)
import "./styles/date.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <DateApp />
  </StrictMode>,
);
