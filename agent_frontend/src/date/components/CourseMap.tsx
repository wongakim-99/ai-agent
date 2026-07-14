import { useEffect, useRef, useState } from "react";
import type { MapPlace } from "../types";

// 네이버 지도 Dynamic Map SDK 를 딱 한 번만 로드하는 싱글턴 로더.
// NCP 통합 콘솔로 발급한 Client ID → ncpKeyId 파라미터.
let sdkPromise: Promise<any> | null = null;

function loadNaver(clientId: string): Promise<any> {
  if (window.naver?.maps) return Promise.resolve(window.naver);
  if (sdkPromise) return sdkPromise;
  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=${clientId}`;
    script.onload = () => resolve(window.naver);
    script.onerror = () =>
      reject(new Error("네이버 지도 SDK 로드 실패 (Client ID / Web 도메인 등록 확인)"));
    document.head.appendChild(script);
  });
  return sdkPromise;
}

interface Props {
  clientId: string;
  places: MapPlace[];
}

export function CourseMap({ clientId, places }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const infoRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 지도 1회 생성
  useEffect(() => {
    if (!clientId || !containerRef.current || mapRef.current) return;
    let cancelled = false;
    loadNaver(clientId)
      .then((naver) => {
        if (cancelled || mapRef.current || !containerRef.current) return;
        mapRef.current = new naver.maps.Map(containerRef.current, {
          center: new naver.maps.LatLng(37.5665, 126.978),
          zoom: 12,
        });
        infoRef.current = new naver.maps.InfoWindow({ borderWidth: 0 });
        setReady(true);
      })
      .catch((e) => setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [clientId]);

  // places(또는 지도 준비 상태)가 바뀌면 마커 다시 그림 + 영역 맞춤
  useEffect(() => {
    const naver = window.naver;
    const map = mapRef.current;
    if (!naver?.maps || !map) return;

    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    const pts = places.filter(
      (p): p is MapPlace & { lat: number; lng: number } => p.lat != null && p.lng != null,
    );
    if (pts.length === 0) return;

    const bounds = new naver.maps.LatLngBounds();
    pts.forEach((p, i) => {
      const pos = new naver.maps.LatLng(p.lat, p.lng); // (위도, 경도)
      const marker = new naver.maps.Marker({
        position: pos,
        map,
        icon: {
          content: `<div class="course-pin__inner">${i + 1}</div>`,
          anchor: new naver.maps.Point(14, 14),
        },
      });
      naver.maps.Event.addListener(marker, "click", () => {
        infoRef.current.setContent(
          `<div style="padding:8px 12px;font-size:13px;line-height:1.5;min-width:140px;">
             <b>${i + 1}. ${p.place_name}</b><br/>
             <span style="color:#888">${p.address}</span>
             ${p.url ? `<br/><a href="${p.url}" target="_blank" rel="noreferrer">지도에서 보기 ↗</a>` : ""}
           </div>`,
        );
        infoRef.current.open(map, marker);
      });
      markersRef.current.push(marker);
      bounds.extend(pos);
    });
    map.fitBounds(bounds, { top: 48, right: 48, bottom: 48, left: 48 });
  }, [places, ready]);

  if (!clientId) {
    return <div className="map map--empty">네이버 지도 Client ID가 없어 지도를 표시할 수 없습니다.</div>;
  }
  if (error) {
    return <div className="map map--empty">지도 로드 실패: {error}</div>;
  }
  return <div className="map" ref={containerRef} />;
}
