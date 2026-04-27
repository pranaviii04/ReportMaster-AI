/**
 * ReportMaster AI — Query History Sidebar
 *
 * Left sidebar displaying the session's query history.  Allows accounting
 * team members to revisit and re-run past questions without retyping them —
 * important for repetitive reporting workflows.
 *
 * Also renders a knowledge-base status card at the bottom showing how many
 * document chunks are indexed and which ChromaDB collection is active.
 *
 * @param {Object}   props
 * @param {Array}    props.history  — Array of { id, question, timestamp }.
 * @param {Function} props.onSelect — Called with question string on click.
 * @param {Function} props.onClear  — Clears all history entries.
 * @param {Object|null} props.stats — { total_documents, collection_name } or null.
 */

import React from "react";

/* ── Timestamp formatter ────────────────────────────────────────────────────── */

function formatTimestamp(date) {
  const now = new Date();
  const diff = Math.floor((now - new Date(date)) / 1000);
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  const h = new Date(date).getHours().toString().padStart(2, "0");
  const m = new Date(date).getMinutes().toString().padStart(2, "0");
  return `Today ${h}:${m}`;
}

/* ── Component ──────────────────────────────────────────────────────────────── */

function QueryHistory({ history, onSelect, onClear, stats }) {
  /* Show most-recent first */
  const reversed = [...history].reverse();

  return (
    <aside className="w-[260px] flex-shrink-0 bg-[#F1F3F5] border-r border-[#E2E8F0] flex flex-col h-full">
      {/* ── Top: history list ────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {/* Header row */}
        <div className="px-4 pt-4 pb-2 flex items-center justify-between">
          <span className="text-xs font-semibold text-[#718096] uppercase tracking-wider">
            History
          </span>
          {history.length > 0 && (
            <button
              type="button"
              onClick={onClear}
              className="text-[10px] text-[#718096] hover:text-[#DC2626] transition-colors"
            >
              Clear all
            </button>
          )}
        </div>

        {/* Empty state */}
        {history.length === 0 && (
          <p className="text-xs text-[#A0AEC0] px-4 py-6 text-center">
            No queries yet. Ask a question to get started.
          </p>
        )}

        {/* History items */}
        {reversed.map((entry) => (
          <button
            key={entry.id}
            type="button"
            onClick={() => onSelect(entry.question)}
            className="w-full text-left px-4 py-2.5 hover:bg-white hover:shadow-sm rounded-lg mx-1 transition-all group"
            style={{ maxWidth: "calc(100% - 8px)" }}
          >
            <span className="text-xs text-[#1A202C] line-clamp-2 leading-relaxed group-hover:text-[#2563EB] transition-colors">
              {entry.question}
            </span>
            <span className="text-[10px] text-[#A0AEC0] mt-0.5 block">
              {formatTimestamp(entry.timestamp)}
            </span>
          </button>
        ))}
      </div>

      {/* ── Bottom: KB status card ───────────────────────────────────────── */}
      <div className="border-t border-[#E2E8F0] p-4">
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-3">
          {stats === null && (
            <span className="text-[10px] text-[#A0AEC0]">
              Checking knowledge base...
            </span>
          )}

          {stats !== null && stats.total_documents > 0 && (
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] inline-block" />
                <span className="text-[10px] text-[#16A34A] font-medium">
                  Knowledge base active
                </span>
              </div>
              <p className="text-[10px] text-[#718096]">
                {stats.total_documents.toLocaleString()} chunks indexed
              </p>
              <p className="text-[10px] text-[#A0AEC0]">
                Collection: {stats.collection_name}
              </p>
            </div>
          )}

          {stats !== null && stats.total_documents === 0 && (
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
                <span className="text-[10px] text-amber-600 font-medium">
                  Knowledge base empty
                </span>
              </div>
              <p className="text-[10px] text-[#718096]">
                Run ingestion script to index manuals
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default QueryHistory;
