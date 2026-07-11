import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

const KEY = "viewer-theme";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function initialTheme(): Theme {
  const saved = localStorage.getItem(KEY);
  return saved === "light" || saved === "dark" ? saved : systemTheme();
}

// 명시 토글 + localStorage 저장. 저장값이 없으면 시스템 설정을 실시간 추종한다.
export function useTheme(): { theme: Theme; toggle: () => void } {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  // data-theme 을 항상 문서에 반영(index.html 인라인 스크립트와 동일 규약).
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // 저장값이 없을 때만 시스템 변경을 따라간다.
  useEffect(() => {
    if (localStorage.getItem(KEY)) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setTheme(systemTheme());
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const toggle = () => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem(KEY, next);
      return next;
    });
  };

  return { theme, toggle };
}
