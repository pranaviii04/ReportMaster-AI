/**
 * ReportMaster AI — API Service Layer
 *
 * All backend communication is centralised here so components never import
 * axios directly.  Handles base URL resolution, request timeouts, and
 * unified error extraction from FastAPI's error response format.
 *
 * Base URL resolves in order:
 *   1. REACT_APP_API_URL environment variable (production / staging)
 *   2. http://localhost:8000 (local development default)
 */

import axios from "axios";

// ── Axios Instance ─────────────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ── Response Interceptor ───────────────────────────────────────────────────────
// Extracts the human-readable error detail from FastAPI's JSON error responses
// and converts network-level failures into a user-friendly message.

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const detail =
        error.response.data?.detail ||
        error.response.data?.message ||
        "Server error";
      throw new Error(detail);
    }
    throw new Error("Network error — is the backend running?");
  }
);

// ── API Functions ──────────────────────────────────────────────────────────────

/**
 * Submit a financial reporting question to the RAG pipeline.
 *
 * POST /api/query
 * Body: { question: string }
 *
 * @param {string} question — Natural-language accounting question (3–500 chars).
 * @returns {Promise<{answer: string, sources: Array, query: string}>}
 */
export const queryFinancialManual = async (question) => {
  const response = await apiClient.post("/api/query", { question });
  return response.data;
};

/**
 * Check if the backend and knowledge base are online.
 *
 * GET /api/health
 * @returns {Promise<{status: string, collection_loaded: boolean}>}
 */
export const getHealth = async () => {
  const response = await apiClient.get("/api/health");
  return response.data;
};

/**
 * Fetch knowledge base stats for the sidebar footer.
 *
 * GET /api/stats
 * @returns {Promise<{total_documents: number, collection_name: string}>}
 */
export const getStats = async () => {
  const response = await apiClient.get("/api/stats");
  return response.data;
};

/**
 * Trigger re-ingestion of financial manuals (admin action).
 *
 * POST /api/ingest
 * @returns {Promise<{message: string, documents_indexed: number}>}
 */
export const triggerIngest = async () => {
  const response = await apiClient.post("/api/ingest");
  return response.data;
};

export default apiClient;
