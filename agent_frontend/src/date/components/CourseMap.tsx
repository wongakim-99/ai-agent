import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { MapPlace } from "../types";

// 무료 OpenStreetMap + Leaflet 로 지도를 그린다 (API 키/가입/카드 전부 불필요).
// 코스 순서를 핀 위 숫자로 보여주는 divIcon 을 써서 기본 마커 이미지 의존도 없앴다.

interface Props {
  places: MapPlace[];
}

function numberedIcon(n: number): L.DivIcon {
  return L.divIcon({
    className: "course-pin",
    html: `<div class="course-pin__inner">${n}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

export function CourseMap({ places }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  // 지도 1회 생성 (OSM 타일)
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current).setView([37.5665, 126.978], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    // flex 레이아웃에서 초기 크기 계산이 어긋날 수 있어 한 번 보정
    setTimeout(() => map.invalidateSize(), 0);
    return () => {
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  // places 바뀌면 마커 다시 그림 + 영역 맞춤
  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();

    const pts = places.filter(
      (p): p is MapPlace & { lat: number; lng: number } => p.lat != null && p.lng != null,
    );
    if (pts.length === 0) return;

    const latlngs: L.LatLngExpression[] = [];
    pts.forEach((p, i) => {
      const marker = L.marker([p.lat, p.lng], { icon: numberedIcon(i + 1) }).addTo(layer);
      marker.bindPopup(
        `<div style="font-size:13px;line-height:1.5;">
           <b>${i + 1}. ${p.place_name}</b><br/>
           <span style="color:#888">${p.address}</span>
           ${p.url ? `<br/><a href="${p.url}" target="_blank" rel="noreferrer">지도에서 보기 ↗</a>` : ""}
         </div>`,
      );
      latlngs.push([p.lat, p.lng]);
    });
    map.fitBounds(L.latLngBounds(latlngs), { padding: [40, 40], maxZoom: 15 });
  }, [places]);

  return <div className="map" ref={containerRef} />;
}
