import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(
      `Making ${config.method?.toUpperCase()} request to ${config.url}`
    );
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const strategyAPI = {
  // Cash-Secured Put candidates
  getCSPCandidates: async (ticker, minRoi = 1.0, minDte = 7, maxDte = 45) => {
    const response = await api.get("/api/strategy/csp/polygon", {
      params: {
        ticker,
        min_roi: minRoi,
        min_dte: minDte,
        max_dte: maxDte,
      },
    });
    return response.data;
  },

  // Covered Call candidates
  getCCCandidates: async (ticker, minRoi = 1.0, minDte = 7, maxDte = 45) => {
    const response = await api.get("/api/strategy/cc/polygon", {
      params: {
        ticker,
        min_roi: minRoi,
        min_dte: minDte,
        max_dte: maxDte,
      },
    });
    return response.data;
  },
};

export default api;
