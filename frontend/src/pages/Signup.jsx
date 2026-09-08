import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_URL } from "../config";

function Signup() {
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const response = await fetch(
                `${API_URL}/auth/signup`,
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
                    data.detail || "Signup failed."
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
                                ? "Creating account..."
                                : "Create account"
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