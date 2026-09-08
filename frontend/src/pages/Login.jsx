import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
    Eye,
    EyeOff
} from "lucide-react";
import { API_URL } from "../config";
import GoogleLoginButton from "../components/GoogleLoginButton";

function Login() {
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [showPassword, setShowPassword] = useState(false);

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const response = await fetch(
                `${API_URL}/auth/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Login failed."
                );
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
                            WELCOME BACK
                        </p>

                        <h1>Sign in to AgentSwarm</h1>

                        <p>
                            Continue working on your tasks with your AI team.
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

                            <div className="password-input-wrapper">

                                <input
                                    id="password"
                                    type={
                                        showPassword
                                            ? "text"
                                            : "password"
                                    }
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(event) =>
                                        setPassword(
                                            event.target.value
                                        )
                                    }
                                    required
                                />

                                <button
                                    type="button"
                                    className="password-toggle"
                                    onClick={() =>
                                        setShowPassword(
                                            (previous) =>
                                                !previous
                                        )
                                    }
                                    aria-label={
                                        showPassword
                                            ? "Hide password"
                                            : "Show password"
                                    }
                                    title={
                                        showPassword
                                            ? "Hide password"
                                            : "Show password"
                                    }
                                >

                                    {showPassword ? (
                                        <EyeOff
                                            size={18}
                                            strokeWidth={1.8}
                                        />
                                    ) : (
                                        <Eye
                                            size={18}
                                            strokeWidth={1.8}
                                        />
                                    )}

                                </button>

                            </div>
                        </div>

                        <div className="forgot-password">
                            <Link to="/forgot-password">
                                Forgot your password?
                            </Link>
                        </div>

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
                                ? "Signing in..."
                                : "Sign in"
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
                        Don't have an account?{" "}

                        <Link to="/signup">
                            Create one
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

export default Login;