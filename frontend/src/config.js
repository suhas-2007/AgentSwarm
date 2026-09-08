// ==============================================================================
// AgentSwarm Frontend Configuration
// ==============================================================================
// In production, VITE_API_URL points to the deployed FastAPI backend.
// In local development, it defaults to http://127.0.0.1:8000.
// ==============================================================================

export const API_URL = (
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
