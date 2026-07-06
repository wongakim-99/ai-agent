import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// dev 서버(5173)가 백엔드(8000)로 API/SSE 를 프록시한다 → 브라우저는 same-origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/graphs": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
