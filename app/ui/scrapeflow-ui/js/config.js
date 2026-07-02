window.ScrapeFlowConfig = {
  API_BASE_URL: localStorage.getItem("sf_api_base_url") || (window.location.origin.startsWith("http") ? window.location.origin : "http://localhost:8000"),
  USE_MOCK: localStorage.getItem("sf_use_mock") === "true",
  STORAGE_PREFIX: "scrapeflow:",
};
