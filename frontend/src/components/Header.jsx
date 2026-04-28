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
    <header className="h-16 flex-shrink-0 sticky top-0 z-50 flex items-center justify-between px-8 bg-[#0F172A] border-b border-white/5 shadow-lg">
      {/* ── Left: Brand ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3">
        {/* Document icon */}
        <div className="p-2 bg-blue-50 rounded-lg">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#2563EB"
            strokeWidth="2.5"
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
        </div>

        <div className="flex flex-col -space-y-0.5">
          <span className="text-sm font-extrabold text-white tracking-tight">
            ReportMaster AI
          </span>
          <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">
            PRO EDITION
          </span>
        </div>
      </div>

      {/* ── Right: Status ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full border border-emerald-100">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Live</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium text-slate-500">Powered by</span>
          <div className="px-2 py-0.5 bg-white/5 rounded-md border border-white/10">
            <span className="text-[11px] font-bold text-slate-300">Google Gemini</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
