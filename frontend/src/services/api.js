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
  baseURL: process.env.REACT_APP_API_URL || "http://127.0.0.1:8000",
  timeout: 300000, // 5 minutes for long RAG queries
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ── Request Interceptor ────────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor ───────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const detail =
        error.response.data?.detail ||
        error.response.data?.message ||
        `Server error (${error.response.status})`;
      throw new Error(detail);
    }
    
    if (error.code === "ECONNABORTED") {
      throw new Error("Request timed out — the RAG pipeline is taking a long time. Please wait a moment.");
    }

    throw new Error("Network error — ensure the backend is running at http://127.0.0.1:8000");
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

/**
 * Upload a PDF manual and trigger indexing.
 *
 * POST /api/upload
 * @param {File} file — PDF file object.
 * @returns {Promise<{message: string, documents_indexed: number}>}
 */
export const uploadManual = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  
  const response = await apiClient.post("/api/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export default apiClient;
