/**
 * ReportMaster AI — Loading Indicator Component
 *
 * Skeleton loading state shown while the RAG pipeline retrieves and generates
 * an answer.  Mimics the shape of an assistant message (avatar + three pulse
 * bars) so the layout does not shift when the real answer arrives.
 *
 * Includes a small spinner and "Searching financial manuals..." status text
 * to reassure the accounting team member that work is in progress.
 */

import React from "react";

function LoadingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      {/* Avatar skeleton */}
      <div className="w-8 h-8 rounded-full bg-[#E2E8F0] flex-shrink-0" />

      {/* Content skeleton */}
      <div className="flex-1 max-w-2xl">
        <div className="bg-white border border-[#E2E8F0] rounded-2xl rounded-tl-sm px-4 py-4">
          <div className="animate-pulse space-y-2">
            <div className="h-3 bg-[#E2E8F0] rounded w-3/4" />
            <div className="h-3 bg-[#E2E8F0] rounded w-full" />
            <div className="h-3 bg-[#E2E8F0] rounded w-1/2" />
          </div>
        </div>

        {/* Status text with spinner */}
        <div className="flex items-center gap-1.5 mt-2">
          <svg
            className="animate-spin h-3 w-3"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="#CBD5E0"
              strokeWidth="3"
            />
            <path
              d="M12 2a10 10 0 0 1 10 10"
              stroke="#2563EB"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
          <span className="text-[10px] text-[#A0AEC0]">
            Searching financial manuals...
          </span>
        </div>
      </div>
    </div>
  );
}

export default LoadingIndicator;
