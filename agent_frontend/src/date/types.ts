// 백엔드 schemas.py (DatePlanOut/CourseStop/MapPlace/DateConfigOut) 와 1:1 대응.

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
}

export interface DateConfig {
  naverMapsClientId: string;
}

// 채팅 대화의 한 메시지 (사용자 입력 or 에이전트 추천 결과)
export type ChatMessage =
  | { id: number; role: "user"; text: string }
  | { id: number; role: "assistant"; result: DatePlanResult };

// 네이버 지도 Dynamic Map SDK 는 <script> 로 로드되어 전역(window.naver)에 얹힌다.
declare global {
  interface Window {
    naver: any;
  }
}
