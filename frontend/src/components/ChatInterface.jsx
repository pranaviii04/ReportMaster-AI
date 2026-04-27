/**
 * ReportMaster AI — Chat Interface Component
 *
 * Primary chat interface for the accounting assistant.  Renders:
 *   • Empty state with suggested questions (before first query)
 *   • Message thread with user bubbles (right) and assistant bubbles (left)
 *   • Collapsible source citations on assistant messages
 *   • Skeleton loading indicator while the RAG pipeline runs
 *   • Error banner when the backend is unreachable
 *   • Auto-growing textarea input bar fixed at the bottom
 *
 * @param {Object}   props
 * @param {Array}    props.messages  — Chat message array from App state.
 * @param {boolean}  props.isLoading — True while awaiting API response.
 * @param {string|null} props.error  — Error message string, or null.
 * @param {Function} props.onQuery   — Handler to submit a new question.
 */

import React, { useState, useRef, useEffect } from "react";
import SourceCard from "./SourceCard";
import LoadingIndicator from "./LoadingIndicator";

/* ── Auto-grow textarea helper ──────────────────────────────────────────────── */

const handleTextareaInput = (e) => {
  e.target.style.height = "auto";
  e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
};

/* ── Suggested questions ────────────────────────────────────────────────────── */

const SUGGESTIONS = [
  "What are the revenue recognition criteria under ASC 606?",
  "How should lease liabilities be disclosed in financial statements?",
  "What is the procedure for correcting prior period errors?",
];

/* ── Component ──────────────────────────────────────────────────────────────── */

function ChatInterface({ messages, isLoading, error, onQuery }) {
  const [inputValue, setInputValue] = useState("");
  const [expandedSources, setExpandedSources] = useState({});

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  /* Auto-scroll to bottom on new messages or loading state changes */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  /* Focus input after assistant responds */
  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus();
    }
  }, [isLoading]);

  /* ── Handlers ─────────────────────────────────────────────────────────────── */

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;
    onQuery(trimmed);
    setInputValue("");
    /* Reset textarea height */
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  /* ── Format timestamp ─────────────────────────────────────────────────────── */

  const formatTime = (date) => {
    const d = new Date(date);
    const h = d.getHours().toString().padStart(2, "0");
    const m = d.getMinutes().toString().padStart(2, "0");
    return `${h}:${m}`;
  };

  /* ── Render ───────────────────────────────────────────────────────────────── */

  const showEmptyState = messages.length === 0 && !isLoading;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* ── Messages / Empty State Area ──────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {/* ── Empty State ────────────────────────────────────────────────── */}
        {showEmptyState && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            {/* Document + magnifier icon */}
            <div className="mb-5 opacity-20">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#2563EB"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
                <path d="M14 2v6h6" />
                <circle cx="11.5" cy="14.5" r="2.5" />
                <path d="M13.3 16.3 15 18" />
              </svg>
            </div>

            <h2 className="text-xl font-semibold text-[#1A202C]">
              Financial Reporting Assistant
            </h2>
            <p className="text-sm text-[#718096] mt-2 max-w-sm">
              Ask any question about your accounting standards and reporting
              procedures.
            </p>

            {/* Divider */}
            <div className="w-16 border-t border-[#E2E8F0] my-6" />

            {/* Suggestion label */}
            <span className="text-xs font-medium text-[#718096] uppercase tracking-wider mb-3">
              Suggested questions
            </span>

            {/* Suggestion pills */}
            <div className="flex flex-col gap-2 max-w-md w-full">
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => onQuery(q)}
                  className="w-full text-left border border-[#E2E8F0] rounded-lg px-4 py-3 text-xs text-[#4A5568] hover:bg-[#F8F9FA] hover:border-[#2563EB] hover:text-[#2563EB] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Message Thread ─────────────────────────────────────────────── */}
        {messages.map((msg) => (
          <div key={msg.id} className="mb-4">
            {msg.type === "user" ? (
              /* ── User Message (right-aligned) ─────────────────────────── */
              <div className="flex justify-end">
                <div className="max-w-lg">
                  <div className="bg-[#2563EB] text-white rounded-2xl rounded-tr-sm px-4 py-3">
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  </div>
                  <p className="text-[10px] text-[#718096] mt-1 text-right">
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            ) : (
              /* ── Assistant Message (left-aligned) ─────────────────────── */
              <div className="flex justify-start gap-3">
                {/* Avatar */}
                <div className="w-8 h-8 rounded-full bg-[#EFF6FF] border border-[#DBEAFE] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-[10px] font-bold text-[#2563EB]">
                    RM
                  </span>
                </div>

                <div className="max-w-2xl flex-1">
                  {/* Answer bubble */}
                  <div className="bg-white border border-[#E2E8F0] rounded-2xl rounded-tl-sm px-4 py-3">
                    <p className="text-sm text-[#1A202C] leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </p>
                  </div>

                  {/* Sources toggle */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-1.5">
                      <button
                        type="button"
                        onClick={() => toggleSources(msg.id)}
                        className="text-xs text-[#2563EB] hover:underline flex items-center gap-1 transition-colors"
                      >
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className={`transition-transform ${expandedSources[msg.id] ? "rotate-180" : ""}`}
                          aria-hidden="true"
                        >
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                        {expandedSources[msg.id]
                          ? "Hide sources"
                          : `${msg.sources.length} source${msg.sources.length !== 1 ? "s" : ""}`}
                      </button>

                      {/* Expanded source cards */}
                      {expandedSources[msg.id] &&
                        msg.sources.map((src, idx) => (
                          <SourceCard
                            key={`${msg.id}-src-${idx}`}
                            doc_title={src.doc_title}
                            content={src.content}
                            score={src.score}
                            index={idx + 1}
                          />
                        ))}
                    </div>
                  )}

                  {/* Timestamp */}
                  <p className="text-[10px] text-[#718096] mt-1">
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* ── Loading skeleton ───────────────────────────────────────────── */}
        {isLoading && <LoadingIndicator />}

        {/* ── Error banner ───────────────────────────────────────────────── */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg mx-0 mb-2">
            {error}
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* ── Input Bar ────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 bg-white border-t border-[#E2E8F0] px-4 py-3">
        <form
          onSubmit={handleSubmit}
          className="flex items-end gap-3 max-w-3xl mx-auto"
        >
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onInput={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask about financial reporting standards..."
              disabled={isLoading}
              className="w-full resize-none border border-[#E2E8F0] rounded-lg px-4 py-3 text-sm text-[#1A202C] placeholder-[#A0AEC0] focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
            />
            <p className="text-[10px] text-[#A0AEC0] mt-1">
              Press Enter to send · Shift+Enter for new line
            </p>
          </div>

          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="bg-[#2563EB] hover:bg-[#1D4ED8] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 text-sm font-medium transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="3"
                  opacity="0.25"
                />
                <path
                  d="M12 2a10 10 0 0 1 10 10"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            ) : (
              "Send"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;
