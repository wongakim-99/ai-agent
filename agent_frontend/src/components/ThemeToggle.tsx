import type { Theme } from "../hooks/useTheme";

interface Props {
  theme: Theme;
  onToggle: () => void;
}

// 헤더 우측 다크/라이트 토글. 클릭하면 반대 테마로 전환(현재 상태를 아이콘으로 표시).
export function ThemeToggle({ theme, onToggle }: Props) {
  const isDark = theme === "dark";
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      title={isDark ? "라이트 모드로" : "다크 모드로"}
      aria-label="테마 전환"
    >
      {isDark ? "☾" : "☀"}
    </button>
  );
}
