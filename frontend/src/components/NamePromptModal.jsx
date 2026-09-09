import { useState, useEffect } from "react";
import { User, X } from "lucide-react";
import { API_URL } from "../config";

export default function NamePromptModal({
    isOpen,
    onClose,
    currentName,
    onSaveSuccess
}) {
    const [name, setName] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (isOpen) {
            setName(currentName || "");
            setError("");
        }
    }, [isOpen, currentName]);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        const trimmed = name.trim();
        if (!trimmed) {
            setError("Please enter a name.");
            return;
        }

        setLoading(true);
        setError("");

        try {
            const token = localStorage.getItem("access_token");
            if (token) {
                const res = await fetch(`${API_URL}/auth/profile`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({ name: trimmed })
                });

                if (!res.ok) {
                    const data = await res.json().catch(() => ({}));
                    throw new Error(data.detail || "Failed to update profile.");
                }
            }

            localStorage.setItem("user_name", trimmed);
            if (onSaveSuccess) onSaveSuccess(trimmed);
            onClose();
        } catch (err) {
            setError(err.message || "Failed to save name.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="name-modal-overlay" onClick={currentName ? onClose : undefined}>
            <div className="name-modal" onClick={(e) => e.stopPropagation()}>
                <div className="name-modal-header">
                    <div className="name-modal-icon">
                        <User size={22} />
                    </div>
                    {currentName && (
                        <button
                            type="button"
                            className="api-keys-close-btn"
                            onClick={onClose}
                            title="Close"
                        >
                            <X size={18} />
                        </button>
                    )}
                </div>

                <h2>{currentName ? "Update your name" : "What should we call you?"}</h2>
                <p>
                    {currentName
                        ? "Change how your AI swarm team addresses you in your workspace."
                        : "Tell us your name so your AI team knows who they're working with."}
                </p>

                <form onSubmit={handleSubmit}>
                    <input
                        type="text"
                        className="name-modal-input"
                        placeholder="e.g. Alex"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        autoFocus
                        maxLength={50}
                        required
                    />

                    {error && <div className="name-modal-error">{error}</div>}

                    <div className="name-modal-actions">
                        {currentName && (
                            <button
                                type="button"
                                className="name-modal-cancel"
                                onClick={onClose}
                                disabled={loading}
                            >
                                Cancel
                            </button>
                        )}
                        <button
                            type="submit"
                            className="name-modal-save"
                            disabled={loading || !name.trim()}
                        >
                            {loading ? "Saving..." : currentName ? "Save changes" : "Continue"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
