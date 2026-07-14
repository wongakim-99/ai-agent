import { useEffect, useRef, useState } from "react";
import type { MapPlace } from "../types";

// Kakao 지도 SDK 를 딱 한 번만 로드하는 싱글턴 로더 (autoload=false → kakao.maps.load).
let sdkPromise: Promise<any> | null = null;

function loadKakao(jsKey: string): Promise<any> {
  if (window.kakao?.maps) return Promise.resolve(window.kakao);
  if (sdkPromise) return sdkPromise;
  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${jsKey}&autoload=false`;
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao));
    script.onerror = () => reject(new Error("Kakao 지도 SDK 로드 실패 (JS 키/도메인 등록 확인)"));
    document.head.appendChild(script);
  });
  return sdkPromise;
}

interface Props {
  jsKey: string;
  places: MapPlace[];
}

export function CourseMap({ jsKey, places }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const infoRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1) SDK 로드 + 지도 1회 생성
  useEffect(() => {
    if (!jsKey || !containerRef.current) return;
    let cancelled = false;
    loadKakao(jsKey)
      .then((kakao) => {
        // StrictMode 이중 실행/중복 생성 방지
        if (cancelled || mapRef.current || !containerRef.current) return;
        mapRef.current = new kakao.maps.Map(containerRef.current, {
          center: new kakao.maps.LatLng(37.5665, 126.978), // 서울시청 (초기값)
          level: 5,
        });
        infoRef.current = new kakao.maps.InfoWindow({ removable: true });
        setReady(true);
      })
      .catch((e) => setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [jsKey]);

  // 2) places(또는 지도 준비 상태)가 바뀌면 마커 다시 그림
  useEffect(() => {
    const kakao = window.kakao;
    const map = mapRef.current;
    if (!kakao?.maps || !map) return;

    // 이전 마커 제거
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    const pts = places.filter((p) => p.lat != null && p.lng != null);
    if (pts.length === 0) return;

    const bounds = new kakao.maps.LatLngBounds();
    pts.forEach((p, i) => {
      const pos = new kakao.maps.LatLng(p.lat, p.lng); // (lat, lng) = (y, x)
      const marker = new kakao.maps.Marker({ position: pos, map });
      kakao.maps.event.addListener(marker, "click", () => {
        infoRef.current.setContent(
          `<div style="padding:6px 10px;font-size:13px;max-width:220px;line-height:1.5;">
             <b>${i + 1}. ${p.place_name}</b><br/>
             <span style="color:#888">${p.address}</span>
             ${p.url ? `<br/><a href="${p.url}" target="_blank" rel="noreferrer">상세보기 ↗</a>` : ""}
           </div>`,
        );
        infoRef.current.open(map, marker);
      });
      markersRef.current.push(marker);
      bounds.extend(pos);
    });
    map.setBounds(bounds);
  }, [places, ready]);

  if (!jsKey) {
    return <div className="map map--empty">Kakao JS 키가 없어 지도를 표시할 수 없습니다.</div>;
  }
  if (error) {
    return <div className="map map--empty">지도 로드 실패: {error}</div>;
  }
  return <div className="map" ref={containerRef} />;
}
