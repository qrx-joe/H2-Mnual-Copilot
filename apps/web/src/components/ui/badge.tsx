/**
 * 状态徽章 —— 对应原型 .badge（blue/green/orange）。
 * 可访问性约束（PRD §55）：状态同时以文字表达，不只靠颜色。
 */

type Tone = "blue" | "green" | "orange";

const TONES: Record<Tone, string> = {
  blue: "bg-blue-soft text-blue",
  green: "bg-green-soft text-green",
  orange: "bg-orange-soft text-orange",
};

export function Badge({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  return (
    <span
      className={`inline-flex h-[23px] items-center rounded-full px-2 text-[10px] font-semibold ${TONES[tone]}`}
    >
      {children}
    </span>
  );
}
