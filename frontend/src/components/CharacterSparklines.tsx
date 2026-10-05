import React from "react";
import type { CharacterArcs } from "../services/series";

type Props = {
  arcs: CharacterArcs;
  episodesOrder: string[]; // ordered episode ids e.g., ["s01e01", ...]
  characters?: string[]; // optional whitelist
  highlightEpisodeId?: string;
};

const WIDTH = 220;
const HEIGHT = 40;
const PADDING = 6;

export const CharacterSparklines: React.FC<Props> = ({
  arcs,
  episodesOrder,
  characters,
  highlightEpisodeId,
}) => {
  const charactersList = React.useMemo(() => {
    const all = Object.keys(arcs);
    if (characters && characters.length) {
      return all.filter((c) => characters.includes(c));
    }
    // choose top by total presence
    return all
      .map((c) => ({
        c,
        total: arcs[c].reduce((acc, p) => acc + (p.presence_score || 0), 0),
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 8)
      .map((x) => x.c);
  }, [arcs, characters]);

  return (
    <div className="flex flex-col gap-2" role="region" aria-label="Character presence arcs">
      {charactersList.map((name) => (
        <LazySparklineRow
          key={name}
          name={name}
          series={arcs[name] || []}
          order={episodesOrder}
          highlightEpisodeId={highlightEpisodeId}
        />
      ))}
    </div>
  );
};

// Lazy-render sparklines below the fold using IntersectionObserver
function LazySparklineRow({
  name,
  series,
  order,
  highlightEpisodeId,
}: {
  name: string;
  series: { episode_id: string; presence_score: number }[];
  order: string[];
  highlightEpisodeId?: string;
}) {
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "50px" } // Start loading slightly before visible
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className="flex items-center gap-3 min-h-[40px]">
      {isVisible ? (
        <SparklineRow
          name={name}
          series={series}
          order={order}
          highlightEpisodeId={highlightEpisodeId}
        />
      ) : (
        <SkeletonSparklineRow name={name} />
      )}
    </div>
  );
}

function SkeletonSparklineRow({ name }: { name: string }) {
  return (
    <>
      <div className="w-28 text-sm text-gray-400">{name}</div>
      <div className="w-[220px] h-[40px] bg-gray-100 rounded animate-pulse" aria-hidden="true" />
    </>
  );
}

function SparklineRow({
  name,
  series,
  order,
  highlightEpisodeId,
}: {
  name: string;
  series: { episode_id: string; presence_score: number }[];
  order: string[];
  highlightEpisodeId?: string;
}) {
  const pointMap = React.useMemo(() => {
    const m = new Map<string, number>();
    series.forEach((p) => m.set(p.episode_id, p.presence_score || 0));
    return m;
  }, [series]);

  const values = order.map((id) => pointMap.get(id) || 0);
  const maxVal = Math.max(1, ...values);
  const xStep = (WIDTH - PADDING * 2) / Math.max(1, order.length - 1);
  const scaleY = (v: number) => HEIGHT - PADDING - (v / maxVal) * (HEIGHT - PADDING * 2);
  const d = values
    .map((v, i) => {
      const x = PADDING + i * xStep;
      const y = scaleY(v);
      return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");

  const hiIndex = highlightEpisodeId ? order.indexOf(highlightEpisodeId) : -1;
  const hiX =
    hiIndex >= 0 ? PADDING + hiIndex * xStep : -9999; /* move off-canvas if not set */
  const hiY = hiIndex >= 0 ? scaleY(values[hiIndex] || 0) : -9999;

  return (
    <div className="flex items-center gap-3">
      <div className="w-28 text-sm text-gray-800">{name}</div>
      <svg width={WIDTH} height={HEIGHT} role="img" aria-label={`${name} presence sparkline`}>
        <path d={d} fill="none" stroke="#4f46e5" strokeWidth={1.5} />
        <line
          x1={hiX}
          x2={hiX}
          y1={PADDING}
          y2={HEIGHT - PADDING}
          stroke="#ef4444"
          strokeDasharray="2,2"
          strokeWidth={1}
        />
        {/* Hover/selection marker at the matching episode point */}
        {hiIndex >= 0 && (
          <circle cx={hiX} cy={hiY} r={2.5} fill="#ef4444" stroke="white" strokeWidth={0.75} />
        )}
      </svg>
    </div>
  );
}


