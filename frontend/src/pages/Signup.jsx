import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_URL } from "../config";
import GoogleLoginButton from "../components/GoogleLoginButton";

function Signup() {
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [isAccountExists, setIsAccountExists] = useState(false);
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setIsAccountExists(false);
        setLoading(true);

        const cleanEmail = email.trim().toLowerCase();

        try {
            const response = await fetch(
                `${API_URL}/auth/signup`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: cleanEmail,
                        password: password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                let detailMsg = "Signup failed.";
                if (typeof data.detail === "string") {
                    detailMsg = data.detail;
                } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
                    detailMsg = data.detail[0].msg;
                }

                if (
                    response.status === 409 ||
                    detailMsg.toLowerCase().includes("already exists")
                ) {
                    setIsAccountExists(true);
                }

                throw new Error(detailMsg);
            }

            localStorage.setItem(
                "access_token",
                data.access_token
            );

            localStorage.setItem(
                "user_id",
                data.user_id
            );

            localStorage.setItem(
                "user_email",
                data.email
            );

            if (data.name) {
                localStorage.setItem(
                    "user_name",
                    data.name
                );
            }

            if (data.avatar_url) {
                localStorage.setItem(
                    "user_avatar",
                    data.avatar_url
                );
            }

            navigate("/dashboard");

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
                            GET STARTED
                        </p>

                        <h1>Create your account</h1>

                        <p>
                            Create an account and start giving your AI team
                            tasks to work on.
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

                        <div className="form-group">
                            <label htmlFor="password">
                                Password
                            </label>

                            <input
                                id="password"
                                type="password"
                                placeholder="Create a password"
                                value={password}
                                onChange={(event) =>
                                    setPassword(event.target.value)
                                }
                                minLength={8}
                                required
                            />
                        </div>

                        {error && (
                            <div className={`auth-alert ${isAccountExists ? "warning" : "error"}`}>
                                <div className="auth-alert-icon">
                                    {isAccountExists ? "ℹ" : "⚠️"}
                                </div>
                                <div className="auth-alert-body">
                                    <div className="auth-alert-title">
                                        {isAccountExists ? "Account Already Exists" : "Signup Failed"}
                                    </div>
                                    <p className="auth-alert-message">
                                        {error}
                                    </p>
                                    {isAccountExists && (
                                        <Link
                                            to={`/login?email=${encodeURIComponent(email.trim())}`}
                                            className="auth-alert-link"
                                        >
                                            Sign in to your account →
                                        </Link>
                                    )}
                                </div>
                            </div>
                        )}

                        <button
                            type="submit"
                            className="auth-submit"
                            disabled={loading}
                        >
                            {loading
                                ? "Creating account..."
                                : "Create account"
                            }

                            {!loading && (
                                <span>→</span>
                            )}
                        </button>

                    </form>

                    <div className="auth-divider">
                        <span>or continue with</span>
                    </div>

                    <GoogleLoginButton onError={(msg) => setError(msg)} />

                    <p className="auth-switch">
                        Already have an account?{" "}

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

export default Signup;