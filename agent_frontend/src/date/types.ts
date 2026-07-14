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
  kakaoJsKey: string;
}

// Kakao Maps JS SDK 는 <script> 태그로 로드되어 전역(window.kakao)에 얹힌다.
declare global {
  interface Window {
    kakao: any;
  }
}
