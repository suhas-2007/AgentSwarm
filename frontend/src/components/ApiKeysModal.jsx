import { useState, useEffect } from "react";
import { Key, ExternalLink, Check, Eye, EyeOff, X } from "lucide-react";
import { API_URL } from "../config";

export default function ApiKeysModal({ isOpen, onClose }) {
    const [status, setStatus] = useState({
        has_gemini_key: false,
        gemini_key_masked: null,
        has_groq_key: false,
        groq_key_masked: null,
        has_tavily_key: false,
        tavily_key_masked: null
    });

    const [geminiKey, setGeminiKey] = useState("");
    const [groqKey, setGroqKey] = useState("");
    const [tavilyKey, setTavilyKey] = useState("");

    const [showGemini, setShowGemini] = useState(false);
    const [showGroq, setShowGroq] = useState(false);
    const [showTavily, setShowTavily] = useState(false);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    const token = localStorage.getItem("access_token");

    useEffect(() => {
        if (!isOpen) return;

        setMessage("");
        setError("");
        setLoading(true);

        fetch(`${API_URL}/auth/api-keys`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        })
            .then(async (res) => {
                if (!res.ok) throw new Error("Failed to load API keys.");
                return res.json();
            })
            .then((data) => {
                setStatus(data);
                setGeminiKey("");
                setGroqKey("");
                setTavilyKey("");
            })
            .catch((err) => {
                setError(err.message || "Failed to load keys.");
            })
            .finally(() => {
                setLoading(false);
            });
    }, [isOpen, token]);

    if (!isOpen) return null;

    async function handleSave(e) {
        e.preventDefault();
        setMessage("");
        setError("");
        setSaving(true);

        const payload = {};
        if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
        if (groqKey.trim()) payload.groq_api_key = groqKey.trim();
        if (tavilyKey.trim()) payload.tavily_api_key = tavilyKey.trim();

        if (Object.keys(payload).length === 0) {
            setError("Please enter at least one API key to save.");
            setSaving(false);
            return;
        }

        try {
            const res = await fetch(`${API_URL}/auth/api-keys`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to save API keys.");

            setStatus(data);
            setGeminiKey("");
            setGroqKey("");
            setTavilyKey("");
            setMessage("API keys saved successfully! Your personal credits will now be used.");
        } catch (err) {
            setError(err.message || "Could not save keys.");
        } finally {
            setSaving(false);
        }
    }

    async function handleClear() {
        if (!confirm("Remove your personal API keys? The application will fall back to server default quotas.")) return;

        setSaving(true);
        setError("");
        setMessage("");

        try {
            const res = await fetch(`${API_URL}/auth/api-keys`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    gemini_api_key: "",
                    groq_api_key: "",
                    tavily_api_key: ""
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error("Failed to clear keys.");

            setStatus(data);
            setGeminiKey("");
            setGroqKey("");
            setTavilyKey("");
            setMessage("Personal API keys cleared.");
        } catch (err) {
            setError(err.message || "Failed to clear keys.");
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="api-keys-overlay" onClick={onClose}>
            <div className="api-keys-modal" onClick={(e) => e.stopPropagation()}>
                <div className="api-keys-modal-header">
                    <div className="api-keys-header-title">
                        <div className="api-keys-icon-badge">
                            <Key size={20} />
                        </div>
                        <div>
                            <h2>Personal API Keys & Credits</h2>
                            <p>Configure your personal keys to use your own API quotas instead of shared server credits.</p>
                        </div>
                    </div>
                    <button type="button" className="api-keys-close-btn" onClick={onClose}>
                        <X size={18} />
                    </button>
                </div>

                {message && <div className="api-keys-alert success"><Check size={16} /><span>{message}</span></div>}
                {error && <div className="api-keys-alert error"><span>{error}</span></div>}

                {loading ? (
                    <div className="api-keys-loading">Loading key configuration...</div>
                ) : (
                    <form onSubmit={handleSave} className="api-keys-form">
                        {/* Gemini Key */}
                        <div className="api-key-item">
                            <div className="api-key-item-header">
                                <div>
                                    <label>Google Gemini API Key</label>
                                    <span className="api-key-desc">Used for Evaluator agent, RAG ground truth verification, and claim audits.</span>
                                </div>
                                <div className="api-key-status">
                                    {status.has_gemini_key ? (
                                        <span className="badge-active">Active: {status.gemini_key_masked}</span>
                                    ) : (
                                        <span className="badge-inactive">Not configured</span>
                                    )}
                                </div>
                            </div>
                            <div className="api-key-input-row">
                                <input
                                    type={showGemini ? "text" : "password"}
                                    placeholder={status.has_gemini_key ? "Paste new key to replace..." : "AIzaSy..."}
                                    value={geminiKey}
                                    onChange={(e) => setGeminiKey(e.target.value)}
                                />
                                <button type="button" className="toggle-vis-btn" onClick={() => setShowGemini(!showGemini)}>
                                    {showGemini ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                            <a
                                href="https://aistudio.google.com/app/apikey"
                                target="_blank"
                                rel="noreferrer"
                                className="api-key-link"
                            >
                                <span>Get free Gemini API key (Google AI Studio)</span>
                                <ExternalLink size={13} />
                            </a>
                        </div>

                        {/* Groq Key */}
                        <div className="api-key-item">
                            <div className="api-key-item-header">
                                <div>
                                    <label>Groq API Key</label>
                                    <span className="api-key-desc">Powers the Planner, Coder, Content Writer, and Finalizer agents.</span>
                                </div>
                                <div className="api-key-status">
                                    {status.has_groq_key ? (
                                        <span className="badge-active">Active: {status.groq_key_masked}</span>
                                    ) : (
                                        <span className="badge-inactive">Not configured</span>
                                    )}
                                </div>
                            </div>
                            <div className="api-key-input-row">
                                <input
                                    type={showGroq ? "text" : "password"}
                                    placeholder={status.has_groq_key ? "Paste new key to replace..." : "gsk_..."}
                                    value={groqKey}
                                    onChange={(e) => setGroqKey(e.target.value)}
                                />
                                <button type="button" className="toggle-vis-btn" onClick={() => setShowGroq(!showGroq)}>
                                    {showGroq ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                            <a
                                href="https://console.groq.com/keys"
                                target="_blank"
                                rel="noreferrer"
                                className="api-key-link"
                            >
                                <span>Get free fast API key (Groq Console)</span>
                                <ExternalLink size={13} />
                            </a>
                        </div>

                        {/* Tavily Key */}
                        <div className="api-key-item">
                            <div className="api-key-item-header">
                                <div>
                                    <label>Tavily Search API Key</label>
                                    <span className="api-key-desc">Powers real-time web search and live internet research for the Researcher agent.</span>
                                </div>
                                <div className="api-key-status">
                                    {status.has_tavily_key ? (
                                        <span className="badge-active">Active: {status.tavily_key_masked}</span>
                                    ) : (
                                        <span className="badge-inactive">Not configured</span>
                                    )}
                                </div>
                            </div>
                            <div className="api-key-input-row">
                                <input
                                    type={showTavily ? "text" : "password"}
                                    placeholder={status.has_tavily_key ? "Paste new key to replace..." : "tvly-..."}
                                    value={tavilyKey}
                                    onChange={(e) => setTavilyKey(e.target.value)}
                                />
                                <button type="button" className="toggle-vis-btn" onClick={() => setShowTavily(!showTavily)}>
                                    {showTavily ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                            <a
                                href="https://app.tavily.com"
                                target="_blank"
                                rel="noreferrer"
                                className="api-key-link"
                            >
                                <span>Get free search API key (Tavily AI)</span>
                                <ExternalLink size={13} />
                            </a>
                        </div>

                        <div className="api-keys-modal-footer">
                            {(status.has_gemini_key || status.has_groq_key || status.has_tavily_key) && (
                                <button
                                    type="button"
                                    className="api-keys-clear-btn"
                                    onClick={handleClear}
                                    disabled={saving}
                                >
                                    Clear My Keys
                                </button>
                            )}
                            <div style={{ flex: 1 }}></div>
                            <button
                                type="button"
                                className="api-keys-cancel-btn"
                                onClick={onClose}
                            >
                                Close
                            </button>
                            <button
                                type="submit"
                                className="api-keys-save-btn"
                                disabled={saving}
                            >
                                {saving ? "Saving..." : "Save API Keys"}
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
