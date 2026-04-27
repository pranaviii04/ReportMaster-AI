/**
 * ReportMaster AI — Header Component
 *
 * Top navigation bar displaying branding, tool identity, and a live status
 * indicator that reflects the service is online.  Fixed at 56px height with
 * a subtle bottom border matching the enterprise design language.
 */

import React from "react";

function Header() {
  return (
    <header className="h-14 flex-shrink-0 flex items-center justify-between px-6 bg-white border-b border-[#E2E8F0]">
      {/* ── Left: Brand ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2.5">
        {/* Document icon */}
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#2563EB"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
          <path d="M14 2v6h6" />
          <path d="M16 13H8" />
          <path d="M16 17H8" />
          <path d="M10 9H8" />
        </svg>

        <span className="text-base font-semibold text-[#1A202C]">
          ReportMaster AI
        </span>

        <span className="text-[#CBD5E0] select-none">·</span>

        <span className="text-[13px] text-[#718096]">
          Financial Reporting Assistant
        </span>
      </div>

      {/* ── Right: Status ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#16A34A]" />
          </span>
          <span className="text-xs font-medium text-[#16A34A]">Live</span>
        </div>

        <span className="text-[#E2E8F0] select-none">|</span>

        <span className="text-xs text-[#718096]">Powered by GPT-4o-mini</span>
      </div>
    </header>
  );
}

export default Header;
