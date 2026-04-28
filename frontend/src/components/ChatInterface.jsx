/**
 * ReportMaster AI — Chat Interface Component
 *
 * The primary workspace for interacting with the RAG pipeline.
 * Features:
 * - Empty state with interactive suggestion grid.
 * - Real-time chat message thread (User/Assistant).
 * - Multi-line auto-expanding input bar with glassmorphism.
 * - Markdown rendering with remark-gfm for professional output.
 * - Collapsible source citations for grounded transparency.
 */

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/* ── Suggestions ─────────────────────────────────────────────────────────── */

const SUGGESTIONS = [
  "What are the revenue recognition criteria under ASC 606?",
  "How should lease liabilities be disclosed in financial statements?",
  "What is the procedure for correcting prior period errors?",
];

/* ── Helpers ─────────────────────────────────────────────────────────────── */

const formatTime = (date) => {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  }).format(date);
};

/* ── Components ──────────────────────────────────────────────────────────── */

/**
 * SourceCard: A compact citation card for transparency.
 */
function SourceCard({ doc_title, content, score, page_number, index }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 mb-2 last:mb-0 shadow-sm animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex justify-between items-start mb-2">
        <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">
          Source #{index}
        </span>
        <span className="text-[10px] font-medium text-slate-400">
          Match Score: {(score * 100).toFixed(0)}%
        </span>
      </div>
      <h4 className="text-[11px] font-bold text-slate-800 line-clamp-1 mb-1">
        {doc_title} {page_number ? `— Page ${page_number}` : ""}
      </h4>
      <p className="text-[11px] text-slate-500 leading-relaxed italic line-clamp-2">
        "{content}"
      </p>
    </div>
  );
}

/**
 * LoadingIndicator: Pulse animation for AI thinking.
 */
function LoadingIndicator() {
  return (
    <div className="flex justify-start items-center gap-2 mb-6">
      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center animate-pulse">
        <div className="w-4 h-4 bg-blue-400/20 rounded-full" />
      </div>
      <div className="flex gap-1">
        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" />
      </div>
    </div>
  );
}

/* ── Main Component ─────────────────────────────────────────────────────── */

function ChatInterface({ messages, isLoading, error, onQuery }) {
  const [inputValue, setInputValue] = useState("");
  const [expandedSources, setExpandedSources] = useState({});
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Handle textarea auto-resize
  const handleTextareaInput = (e) => {
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    onQuery(inputValue);
    setInputValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  return (
    <div className="flex-1 flex flex-col relative bg-slate-50 overflow-hidden">
      {/* ── Scrollable Area ────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {!messages.length && (
          <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] text-center">
            <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center mb-8 shadow-sm border border-slate-100">
              <svg
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#2563EB"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
                <path d="M14 2v6h6" />
                <circle cx="11.5" cy="14.5" r="2.5" />
                <path d="M13.3 16.3 15 18" />
              </svg>
            </div>

            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Financial Reporting Intelligence
            </h2>
            <p className="text-sm text-slate-500 mt-4 max-w-lg leading-relaxed font-medium">
              Precision-grounded AI for accounting standards, compliance checks, and automated reporting.
            </p>

            <div className="w-12 h-1 bg-blue-600 rounded-full my-10" />

            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.25em] mb-6">
              Quick Inquiries
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl w-full">
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => onQuery(q)}
                  className="group relative w-full text-left bg-white border border-slate-200/60 rounded-2xl px-6 py-5 text-xs font-semibold text-slate-700 hover:border-blue-500/50 hover:text-blue-600 shadow-[0_2px_4px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_24px_rgba(37,99,235,0.1)] transition-all transform hover:-translate-y-1"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <span className="leading-snug">{q}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Message Thread ─────────────────────────────────────────────── */}
        {messages.map((msg) => (
          <div key={msg.id} className="mb-8 last:mb-0">
            {msg.type === "user" ? (
              <div className="flex justify-end">
                <div className="max-w-lg">
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-md">
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-2 text-right font-medium">
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex justify-start gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                  <span className="text-[10px] font-bold text-blue-600">RM</span>
                </div>

                <div className="max-w-2xl flex-1">
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-6 py-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="markdown-content text-[14px] text-slate-800 leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3">
                      <button
                        type="button"
                        onClick={() => toggleSources(msg.id)}
                        className="text-[11px] font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1.5 transition-colors uppercase tracking-wider"
                      >
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className={`transition-transform duration-300 ${expandedSources[msg.id] ? "rotate-180" : ""}`}
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                        {expandedSources[msg.id]
                          ? "Hide Citations"
                          : `View ${msg.sources.length} Grounded Source${msg.sources.length !== 1 ? "s" : ""}`}
                      </button>

                      {expandedSources[msg.id] && (
                        <div className="mt-3 grid gap-2 animate-in fade-in zoom-in-95 duration-200">
                          {msg.sources.map((src, idx) => (
                            <SourceCard
                              key={`${msg.id}-src-${idx}`}
                              doc_title={src.doc_title}
                              content={src.content}
                              score={src.score}
                              page_number={src.page_number}
                              index={idx + 1}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <p className="text-[10px] text-slate-400 mt-2 font-medium">
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && <LoadingIndicator />}

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 text-xs px-4 py-3 rounded-xl mb-6 flex items-center gap-3">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="font-medium">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Fixed Input Area ───────────────────────────────────────────── */}
      <div className="px-6 pb-8 bg-gradient-to-t from-slate-50 via-slate-50/80 to-transparent">
        <div className="max-w-4xl mx-auto relative">
          <form
            onSubmit={handleSubmit}
            className="bg-white border border-slate-200 rounded-3xl shadow-xl focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-500 transition-all overflow-hidden"
          >
            <div className="flex items-end px-6 py-4">
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onInput={handleTextareaInput}
                onKeyDown={handleKeyDown}
                placeholder="Ask about financial reporting standards..."
                disabled={isLoading}
                className="flex-1 bg-transparent border-none focus:ring-0 text-[15px] text-slate-800 placeholder-slate-400 resize-none max-h-32 py-1 leading-relaxed"
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className={`ml-4 p-3 rounded-2xl transition-all flex items-center justify-center ${
                  !inputValue.trim() || isLoading
                    ? "bg-slate-50 text-slate-300"
                    : "bg-blue-600 text-white hover:bg-blue-700 shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:scale-105 active:scale-95"
                }`}
              >
                {isLoading ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                  </svg>
                ) : (
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                )}
              </button>
            </div>
          </form>
          <p className="text-[10px] font-bold text-slate-400 mt-4 text-center uppercase tracking-[0.2em]">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
