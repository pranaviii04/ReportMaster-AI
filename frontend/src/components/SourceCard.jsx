/**
 * ReportMaster AI — Source Card Component
 *
 * Displays a single retrieved source document chunk cited in an answer.
 * Each card represents one section of a financial reporting manual that
 * contributed to the RAG-generated answer above it.
 *
 * Collapsible: shows a short preview by default, expands to full content
 * on toggle.  Score is displayed as a percentage badge.
 *
 * @param {Object} props
 * @param {string} props.doc_title  — Document / company name.
 * @param {string} props.content    — Full chunk text from ChromaDB.
 * @param {number} props.score      — Cosine similarity score (0–1).
 * @param {number} props.index      — 1-based source number for labelling.
 */

import React, { useState } from "react";

function SourceCard({ doc_title, content, score, index }) {
  const [isOpen, setIsOpen] = useState(false);

  const preview =
    content.length > 120 ? content.slice(0, 120) + "..." : content;

  return (
    <div className="bg-[#F8FAFF] border border-[#DBEAFE] rounded-lg p-3 mt-2">
      {/* ── Header Row ──────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        {/* Left: badge + title */}
        <div className="flex items-center min-w-0">
          <span className="flex-shrink-0 bg-[#EFF6FF] text-[#1D4ED8] text-[10px] font-medium px-2 py-0.5 rounded-full">
            Source {index}
          </span>
          <span className="text-xs font-medium text-[#1A202C] ml-2 truncate max-w-[200px]">
            {doc_title}
          </span>
        </div>

        {/* Right: score + toggle */}
        <div className="flex items-center flex-shrink-0">
          <span className="bg-[#EFF6FF] text-[#1D4ED8] text-[10px] font-medium px-2 py-0.5 rounded-full">
            Score: {(score * 100).toFixed(0)}%
          </span>
          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            className="text-[#718096] hover:text-[#1A202C] text-xs ml-2 transition-colors"
          >
            {isOpen ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      {/* ── Preview (always visible when collapsed) ─────────────────────── */}
      {!isOpen && (
        <p className="text-[10px] text-[#718096] mt-1.5 leading-relaxed">
          {preview}
        </p>
      )}

      {/* ── Full Content (expanded) ─────────────────────────────────────── */}
      {isOpen && (
        <div className="border-t border-[#DBEAFE] mt-2 pt-2">
          <p className="text-xs text-[#4A5568] leading-relaxed whitespace-pre-wrap">
            {content}
          </p>
        </div>
      )}
    </div>
  );
}

export default SourceCard;
