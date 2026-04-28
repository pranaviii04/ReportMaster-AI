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

import React, { useRef } from "react";

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

function QueryHistory({ history, onSelect, onClear, onUpload, stats }) {
  const fileInputRef = useRef(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
    // Reset input so the same file can be selected again if needed
    e.target.value = "";
  };
  /* Show most-recent first */
  const reversed = [...history].reverse();

  return (
    <aside className="w-[280px] flex-shrink-0 bg-[#0F172A] flex flex-col h-full border-r border-white/5">
      {/* ── Top: history list ────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 custom-scrollbar">
        {/* Header row */}
        <div className="pt-8 pb-4 flex items-center justify-between">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">
            History
          </span>
          {history.length > 0 && (
            <button
              type="button"
              onClick={onClear}
              className="text-[10px] text-slate-500 hover:text-red-400 transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* Empty state */}
        {history.length === 0 && (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-slate-500 leading-relaxed">
              Your query history will appear here.
            </p>
          </div>
        )}

        {/* History items */}
        <div className="space-y-1 pb-8">
          {reversed.map((entry) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => onSelect(entry.question)}
              className="w-full text-left px-3 py-4 hover:bg-white/[0.03] rounded-xl transition-all group border border-transparent hover:border-white/5"
            >
              <span className="text-xs text-slate-300 line-clamp-2 leading-relaxed group-hover:text-blue-400 transition-colors">
                {entry.question}
              </span>
              <span className="text-[9px] text-slate-600 mt-2 block font-bold uppercase tracking-wider">
                {formatTimestamp(entry.timestamp)}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Bottom: KB status card ───────────────────────────────────────── */}
      <div className="p-4 bg-[#0F172A] border-t border-white/5">
        <div className="bg-gradient-to-b from-slate-800/40 to-slate-900/40 border border-white/5 rounded-2xl p-5">
          {stats === null && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-slate-600 animate-pulse" />
              <span className="text-[11px] text-slate-400">
                Checking status...
              </span>
            </div>
          )}

          {stats !== null && (
            <div className="space-y-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-2 h-2 rounded-full ${stats.total_documents > 0 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500'} `} />
                  <span className={`text-[11px] font-bold ${stats.total_documents > 0 ? 'text-emerald-400' : 'text-amber-400'} uppercase tracking-wider`}>
                    {stats.total_documents > 0 ? 'KB Synced' : 'KB Empty'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">
                  {stats.total_documents.toLocaleString()} semantic chunks
                </p>
              </div>
              
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".pdf"
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={handleUploadClick}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[11px] font-bold py-2.5 rounded-lg hover:shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  Upload Manual (PDF)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default QueryHistory;
