import type { CourseStop } from "../types";

interface Props {
  region: string;
  summary: string;
  course: CourseStop[];
}

const CATEGORY_LABEL: Record<string, string> = {
  restaurant: "맛집",
  cafe: "카페",
  activity: "활동",
};

export function CourseList({ region, summary, course }: Props) {
  if (course.length === 0) {
    return (
      <div className="cl cl--empty">
        추천할 코스를 찾지 못했어요. 다른 지역이나 키워드로 다시 시도해보세요.
      </div>
    );
  }

  return (
    <div className="cl">
      <div className="cl__head">
        <div className="cl__region">📍 {region}</div>
        <p className="cl__summary">{summary}</p>
      </div>
      <ol className="cl__list">
        {course.map((s) => (
          <li key={s.step} className="cl__item">
            <div className="cl__step">{s.step}</div>
            <div className="cl__body">
              <div className="cl__line1">
                <span className={`cl__tag cl__tag--${s.category}`}>
                  {CATEGORY_LABEL[s.category] ?? s.category}
                </span>
                <span className="cl__time">{s.time_slot}</span>
              </div>
              {s.url ? (
                <a className="cl__name" href={s.url} target="_blank" rel="noreferrer">
                  {s.place_name} ↗
                </a>
              ) : (
                <span className="cl__name">{s.place_name}</span>
              )}
              <div className="cl__addr">{s.address}</div>
              <div className="cl__reason">{s.reason}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
