/**
 * 内联图标集 —— path 数据逐项取自原型 SVG symbol（a3739cd9）。
 * 用 currentColor 继承文字色，尺寸由 className 控制（默认 18px，icon-sm 15px）。
 */
import type { SVGProps } from "react";

const PATHS: Record<string, string[]> = {
  spark: [
    "M12 3l1.2 4.1L17 9l-3.8 1.8L12 15l-1.2-4.2L7 9l3.8-1.9L12 3Z",
    "M18.5 13l.7 2.2 2.3.8-2.3.8-.7 2.2-.7-2.2-2.3-.8 2.3-.8.7-2.2Z",
  ],
  book: [
    "M4 5.5A2.5 2.5 0 0 1 6.5 3H11a2 2 0 0 1 2 2v14a2.5 2.5 0 0 0-2.5-2.5H4v-11Z",
    "M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16a2.5 2.5 0 0 1 2.5-2.5H20v-11Z",
  ],
  check: ["m5 12.5 4.1 4L19 7"],
  x: ["m7 7 10 10M17 7 7 17"],
  search: [
    "M10.5 4a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Z",
    "m15.4 15.4 4.1 4.1",
  ],
  doc: [
    "M6 3.5h8l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 5 20V5a1.5 1.5 0 0 1 1-1.5Z",
    "M14 3.5V8h4M8 12h8M8 15h8M8 18h5",
  ],
  grid: [
    "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
  ],
  moon: ["M19.2 15.2A7.8 7.8 0 0 1 8.8 4.8 8.2 8.2 0 1 0 19.2 15.2Z"],
  sun: [
    "M12 8.4a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2Z",
    "M12 2.8v2M12 19.2v2M2.8 12h2M19.2 12h2M5.5 5.5l1.4 1.4M17.1 17.1l1.4 1.4M18.5 5.5l-1.4 1.4M6.9 17.1l-1.4 1.4",
  ],
  menu: ["M5 7h14M5 12h14M5 17h14"],
  down: ["m7 9 5 5 5-5"],
  send: ["M5 12h13M13 7l5 5-5 5"],
  alert: ["M12 3.5 21 19H3L12 3.5Z", "M12 9v4.5M12 16.5v.1"],
  shield: [
    "M12 3.5 19 6v5.5c0 4.4-2.9 7.8-7 9-4.1-1.2-7-4.6-7-9V6l7-2.5Z",
    "m8.5 12 2.1 2.1 4.7-5",
  ],
  copy: [
    "M8 8h11v11H8z",
    "M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2",
  ],
  thumb: [
    "M8 10v10H4.5A1.5 1.5 0 0 1 3 18.5v-7A1.5 1.5 0 0 1 4.5 10H8Zm0 0 3-6c1.4 0 2.2 1.1 2 2.5L12.5 10H19a2 2 0 0 1 2 2.4l-1.1 5.5A2.6 2.6 0 0 1 17.4 20H8",
  ],
  flag: ["M5 21V4M5 5h10l-1.5 3L15 11H5"],
  upload: ["M12 16V4M8 8l4-4 4 4M5 13v5.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V13"],
  more: ["M5 12h.01M12 12h.01M19 12h.01"],
  info: ["M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Z", "M12 10.5V16M12 7.6v.1"],
};

const FILLED = new Set(["spark", "more"]);

export function Icon({
  name,
  className = "h-[18px] w-[18px]",
  ...rest
}: { name: keyof typeof PATHS; className?: string } & SVGProps<SVGSVGElement>) {
  const filled = FILLED.has(name);
  return (
    <svg viewBox="0 0 24 24" className={className} fill={filled ? "currentColor" : "none"} aria-hidden="true" {...rest}>
      {PATHS[name].map((d) => (
        <path
          key={d}
          d={d}
          stroke={filled ? undefined : "currentColor"}
          strokeWidth={filled ? undefined : 1.7}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </svg>
  );
}
