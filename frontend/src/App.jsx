/**
 * ReportMaster AI — Root Application Component
 *
 * Owns all global state: chat messages, query history, loading flag, errors,
 * and knowledge-base statistics.  Renders the fixed-viewport layout shell
 * and passes state + handlers down to child components.
 *
 * State is managed entirely with useState hooks — no external state library.
 * All API communication flows through src/services/api.js.
 */

import React, { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import ChatInterface from "./components/ChatInterface";
import QueryHistory from "./components/QueryHistory";
import { queryFinancialManual, getStats, uploadManual } from "./services/api";

function App() {
  /* ── State ────────────────────────────────────────────────────────────────── */

  /** Chat messages — array of { id, type, content, sources, timestamp } */
  const [messages, setMessages] = useState([]);

  /** Sidebar history — array of { id, question, timestamp } */
  const [history, setHistory] = useState([]);

  /** True while waiting for the RAG pipeline to respond */
  const [isLoading, setIsLoading] = useState(false);

  /** Human-readable error string, or null when healthy */
  const [error, setError] = useState(null);

  /** Knowledge-base stats from GET /api/stats, or null before first fetch */
  const [stats, setStats] = useState(null);

  /* ── Boot: fetch KB stats ─────────────────────────────────────────────────── */

  useEffect(() => {
    getStats()
      .then((data) => setStats(data))
      .catch(() => {
        /* Stats are non-critical — silently ignore fetch failures */
      });
  }, []);

  /* ── Handlers ─────────────────────────────────────────────────────────────── */

  /**
   * Submit a question through the RAG pipeline and append both the user
   * message and the assistant response to the chat thread.
   *
   * @param {string} question — The accounting question to send.
   */
  const handleQuery = useCallback(
    async (question) => {
      const trimmed = question.trim();
      if (!trimmed || isLoading) return;

      /* 1. Append user message */
      const userMsg = {
        id: Date.now(),
        type: "user",
        content: trimmed,
        sources: [],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);

      /* 2. Append history entry (cap at 20) */
      setHistory((prev) => {
        const next = [
          ...prev,
          { id: Date.now(), question: trimmed, timestamp: new Date() },
        ];
        return next.length > 20 ? next.slice(next.length - 20) : next;
      });

      /* 3. Call API */
      setIsLoading(true);
      setError(null);

      try {
        const data = await queryFinancialManual(trimmed);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "assistant",
            content: data.answer,
            sources: data.sources || [],
            timestamp: new Date(),
          },
        ]);
      } catch (err) {
        const errMsg = err.message || "Unknown error";
        setError(errMsg);
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "assistant",
            content:
              "Sorry, I couldn't process your question. " + errMsg,
            sources: [],
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading]
  );

  /**
   * Re-submit a past question from the sidebar history.
   * @param {string} question
   */
  const handleHistoryClick = useCallback(
    (question) => {
      handleQuery(question);
    },
    [handleQuery]
  );

  /** Clear all sidebar history entries. */
  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  /** Upload a PDF manual and refresh stats. */
  const handleUpload = useCallback(async (file) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await uploadManual(file);
      // Refresh stats after successful upload and indexing
      const newStats = await getStats();
      setStats(newStats);
      
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: "assistant",
          content: data.message,
          sources: [],
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /* ── Render ───────────────────────────────────────────────────────────────── */

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-50">
      {/* Fixed top bar */}
      <Header />

      {/* Main content: sidebar + chat */}
      <div className="flex flex-1 overflow-hidden">
        <QueryHistory
          history={history}
          onSelect={handleHistoryClick}
          onClear={clearHistory}
          onUpload={handleUpload}
          stats={stats}
        />
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          error={error}
          onQuery={handleQuery}
        />
      </div>
    </div>
  );
}

export default App;
