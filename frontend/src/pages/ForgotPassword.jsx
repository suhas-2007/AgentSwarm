import { useState } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";

function ForgotPassword() {
    const [email, setEmail] = useState("");

    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setMessage("");
        setError("");
        setLoading(true);

        try {
            const response = await fetch(
                `${API_URL}/auth/forgot-password`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Unable to process request."
                );
            }

            setMessage(
                "If an account exists with this email, password reset instructions have been sent."
            );

        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-container">

                <Link to="/" className="auth-logo">
                    <div className="logo-mark">A</div>
                    <span>AgentSwarm</span>
                </Link>

                <div className="auth-card">

                    <div className="auth-header">
                        <p className="section-label">
                            ACCOUNT RECOVERY
                        </p>

                        <h1>Forgot your password?</h1>

                        <p>
                            Enter your email address and we'll help you
                            reset your password.
                        </p>
                    </div>

                    <form
                        className="auth-form"
                        onSubmit={handleSubmit}
                    >

                        <div className="form-group">
                            <label htmlFor="email">
                                Email
                            </label>

                            <input
                                id="email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(event) =>
                                    setEmail(event.target.value)
                                }
                                required
                            />
                        </div>

                        {message && (
                            <p className="auth-success">
                                {message}
                            </p>
                        )}

                        {error && (
                            <p className="auth-error">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            className="auth-submit"
                            disabled={loading}
                        >
                            {loading
                                ? "Sending..."
                                : "Send reset instructions"
                            }

                            {!loading && (
                                <span>→</span>
                            )}
                        </button>

                    </form>

                    <div className="auth-divider">
                        <span>or</span>
                    </div>

                    <p className="auth-switch">
                        Remember your password?{" "}

                        <Link to="/login">
                            Sign in
                        </Link>
                    </p>

                </div>

                <Link to="/" className="back-home">
                    ← Back to AgentSwarm
                </Link>

            </div>
        </div>
    );
}

export default ForgotPassword;