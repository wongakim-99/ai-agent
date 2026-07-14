import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// dev 서버(5174)가 백엔드(8000)로 API/SSE 를 프록시한다 → 브라우저는 same-origin.
// 멀티페이지: index.html(토폴로지 뷰어) + date.html(데이트 코스 플래너).
// (input 은 상대경로 문자열 — Vite 가 프로젝트 루트 기준으로 해석한다)
// port 는 5174 로 고정(strictPort): 다른 프로젝트(5173)와 충돌 방지 + 네이버 지도 도메인 매칭 예측 가능.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      "/graphs": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/api": "http://localhost:8000", // 데이트 앱: /api/date/* (페이지 /date.html 과 무충돌)
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: "index.html",
        date: "date.html",
      },
    },
  },
});
