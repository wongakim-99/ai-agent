// 백엔드 api/date_planner/dto.py (DatePlanOut/CourseStop/MapPlace/DateStep/DateConfigOut) 와 1:1 대응.

// 에이전트 노드 하나가 무엇을 왜 했는지. 문장(lines)은 백엔드가 실제 값으로 조립한다.
export interface DateStep {
  node: string; // planner | restaurant_agent | cafe_agent | activity_agent | curator
  kind: "planner" | "search" | "curator";
  title: string;
  lines: string[];
}

export interface CourseStop {
  step: number;
  time_slot: string;
  category: string; // restaurant | cafe | activity
  place_name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  url: string;
  reason: string;
}

export interface MapPlace {
  place_name: string;
  address: string;
  lat: number | null;
  lng: number | null;
  url: string;
  category: string;
}

export interface DatePlanResult {
  region: string;
  summary: string;
  course: CourseStop[];
  places: MapPlace[];
  steps: DateStep[];
}

// POST /api/date/plan/stream 이 흘리는 SSE 이벤트 (controller.plan_stream 과 대응).
export type DateRunEvent =
  | { type: "step"; step: DateStep }
  | { type: "done"; result: DatePlanResult }
  | { type: "error"; message: string };

export interface DateConfig {
  naverMapsClientId: string;
}

// 채팅 대화의 한 메시지 (사용자 입력 or 에이전트 추천 결과)
// assistant 메시지는 결과에 steps 를 품고 있어, 실행이 끝난 뒤에도 과정을 되짚어볼 수 있다.
export type ChatMessage =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "assistant"; result: DatePlanResult };

// 네이버 지도 Dynamic Map SDK 는 <script> 로 로드되어 전역(window.naver)에 얹힌다.
declare global {
  interface Window {
    naver: any;
  }
}
