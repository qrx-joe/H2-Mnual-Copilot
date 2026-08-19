"use client";

/**
 * 输入区（原型 .composer + .device 下拉）。
 * 设备/版本选择是 FR-005 的交互入口：回答与设备绑定，切换设备以 toast 明示。
 */

import { useEffect, useRef, useState } from "react";

import { useUI } from "@/components/shell/ui-context";
import { Icon } from "@/components/ui/icon";
import { MOCK_DEVICES } from "@/lib/mock-data";

export function Composer({
  busy,
  onSubmit,
}: {
  busy: boolean;
  onSubmit: (query: string) => void;
}) {
  const { toast } = useUI();
  const [text, setText] = useState("");
  const [device, setDevice] = useState(MOCK_DEVICES[0]);
  const [deviceOpen, setDeviceOpen] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  // 自动增高（原型 oninput 逻辑），上限 150px
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
  }, [text]);

  const submit = () => {
    const q = text.trim();
    if (!q || busy) return;
    setText("");
    onSubmit(q);
  };

  return (
    <div className="absolute bottom-4 left-4 right-4 max-[680px]:bottom-2.5 max-[680px]:left-2.5 max-[680px]:right-2.5">
      <div className="overflow-hidden rounded-[20px] border border-line bg-glass shadow-e2 backdrop-blur-2xl focus-within:border-[rgba(0,113,227,.5)] focus-within:shadow-[0_0_0_4px_rgba(0,113,227,.10),var(--shadow-e2)]">
        <textarea
          id="composer"
          ref={ref}
          rows={1}
          value={text}
          disabled={busy}
          aria-label="输入设备问题、报警代码或操作步骤"
          placeholder="输入设备问题、报警代码或操作步骤…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          className="max-h-[150px] min-h-[62px] w-full resize-none border-0 bg-transparent px-4 pb-1.5 pt-3.5 text-[13px] leading-relaxed outline-none placeholder:text-ink-3 disabled:opacity-60"
        />
        <div className="flex min-h-[45px] items-center gap-1.5 px-2.5 pb-2 pl-2.5">
          {/* 设备/版本选择（FR-005） */}
          <div className="relative">
            <button
              className="inline-flex h-[38px] items-center gap-2 rounded-[10px] border border-line-soft bg-surface-2 px-3 hover:border-line"
              onClick={() => setDeviceOpen((v) => !v)}
              aria-haspopup="listbox"
              aria-expanded={deviceOpen}
            >
              <span className="grid h-6 w-6 place-items-center rounded-lg bg-blue-soft text-blue">
                <Icon name="grid" className="h-[15px] w-[15px]" />
              </span>
              <span className="text-left">
                <strong className="block text-[11px] leading-tight">{device.name}</strong>
                <small className="block text-[9px] leading-tight text-ink-3">Current manual · {device.currentVersion}</small>
              </span>
              <Icon name="down" className="h-[15px] w-[15px] text-ink-3" />
            </button>
            {deviceOpen && (
              <ul
                role="listbox"
                className="absolute bottom-[calc(100%+7px)] left-0 z-50 w-[260px] rounded-[14px] border border-line-soft bg-surface p-1.5 shadow-e3"
              >
                {MOCK_DEVICES.map((d) => (
                  <li key={d.id}>
                    <button
                      role="option"
                      aria-selected={d.id === device.id}
                      className={`flex w-full items-center gap-2 rounded-lg p-2 text-left hover:bg-surface-3 ${
                        d.id === device.id ? "bg-surface-3" : ""
                      }`}
                      onClick={() => {
                        setDevice(d);
                        setDeviceOpen(false);
                        toast({ tone: "info", title: "Device context updated", message: `${d.name} · ${d.currentVersion}` });
                      }}
                    >
                      <span className="min-w-0 flex-1">
                        <strong className="block text-[11px]">{d.name}</strong>
                        <small className="block text-[9px] text-ink-3">Current manual · {d.currentVersion}</small>
                      </span>
                      {d.id === device.id && <Icon name="check" className="h-[15px] w-[15px] text-blue" />}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Evidence required：MVP 固定开启（不可关闭——工业场景不允许放松证据约束） */}
          <span className="inline-flex h-[33px] items-center gap-1.5 rounded-full border border-[rgba(0,113,227,.25)] bg-blue-soft px-3 text-[11px] font-semibold text-blue max-[430px]:hidden">
            <Icon name="shield" className="h-[15px] w-[15px]" />
            Evidence required
          </span>

          <span className="ml-auto hidden text-[9px] text-ink-3 md:block">Enter 发送 · Shift + Enter 换行</span>
          <button
            aria-label="发送问题"
            className="grid h-[34px] w-[34px] place-items-center rounded-full bg-blue text-white hover:bg-blue-hover disabled:cursor-not-allowed disabled:opacity-40"
            disabled={busy || !text.trim()}
            onClick={submit}
          >
            <Icon name="send" />
          </button>
        </div>
      </div>
    </div>
  );
}
