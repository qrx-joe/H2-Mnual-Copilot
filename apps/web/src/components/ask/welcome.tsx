"use client";

/**
 * Ask 欢迎页（原型 .welcome + .quickgrid）。
 * 快捷入口覆盖 Demo 黄金路径四场景；文字取自原型（固定演示数据）。
 */

import { Icon } from "@/components/ui/icon";
import { QUICK_PROMPTS } from "@/lib/mock-data";

const TONE_STYLES: Record<string, string> = {
  blue: "bg-blue-soft text-blue",
  orange: "bg-orange-soft text-orange",
  green: "bg-green-soft text-green",
  red: "bg-red-soft text-red",
};

export function Welcome({ onQuickPick }: { onQuickPick: (query: string) => void }) {
  return (
    <div className="mx-auto mt-12 max-w-[720px] text-center">
      {/* 轨道品牌图标（原型 .orbit） */}
      <div className="relative mx-auto mb-5 grid h-[72px] w-[72px] place-items-center rounded-r3 bg-ink text-surface shadow-e2">
        <span className="absolute h-[20px] w-[55px] rounded-full border border-current opacity-20 rotate-[27deg]" />
        <span className="absolute h-[20px] w-[55px] rounded-full border border-current opacity-20 -rotate-[27deg]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[#5ac8fa] shadow-[0_0_0_6px_rgba(90,200,250,.12)]" />
      </div>
      <h1 className="text-[clamp(32px,5vw,48px)] leading-[1.03] font-semibold tracking-tighter">
        Ask the equipment.
        <br />
        Verify the evidence.
      </h1>
      <p className="mx-auto mt-3.5 max-w-[590px] text-[15px] leading-relaxed text-ink-2">
        从设备手册、维护资料、错误代码与安全文档中获取可追溯答案。资料不足时明确拒答，不替工业参数“自由发挥”。
      </p>

      <div className="mx-auto mt-8 grid max-w-[690px] grid-cols-2 gap-2.5 text-left max-[680px]:grid-cols-1">
        {QUICK_PROMPTS.map((q) => (
          <button
            key={q.title}
            onClick={() => onQuickPick(q.query)}
            className="rounded-r3 border border-line-soft bg-surface-2 p-4 transition-all hover:-translate-y-px hover:border-line hover:bg-surface hover:shadow-e1"
          >
            <div className="mb-1.5 flex items-center gap-2">
              <span className={`grid h-[29px] w-[29px] place-items-center rounded-lg ${TONE_STYLES[q.tone]}`}>
                <Icon name={q.icon} className="h-4 w-4" />
              </span>
              <strong className="text-[12px]">{q.title}</strong>
            </div>
            <p className="text-[11px] leading-normal text-ink-2">{q.desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
