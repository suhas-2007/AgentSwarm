import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { API_URL } from "../config";


function ResetPassword() {

    const [searchParams] = useSearchParams();

    const navigate = useNavigate();

    const token = searchParams.get("token");

    const [password, setPassword] = useState("");

    const [confirmPassword, setConfirmPassword] = useState("");

    const [message, setMessage] = useState("");

    const [error, setError] = useState("");

    const [loading, setLoading] = useState(false);


    async function handleSubmit(event) {

        event.preventDefault();

        setMessage("");
        setError("");

        if (!token) {

            setError(
                "Invalid or missing password reset token."
            );

            return;
        }


        if (password !== confirmPassword) {

            setError(
                "Passwords do not match."
            );

            return;
        }


        if (password.length < 8) {

            setError(
                "Password must be at least 8 characters."
            );

            return;
        }


        setLoading(true);


        try {

            const response = await fetch(
                `${API_URL}/auth/reset-password`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        token: token,
                        new_password: password
                    })
                }
            );


            const data = await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to reset password."
                );
            }


            setMessage(
                "Password reset successfully. Redirecting to login..."
            );


            setTimeout(() => {

                navigate("/login");

            }, 1500);


        } catch (error) {

            setError(
                error.message
            );

        } finally {

            setLoading(false);
        }
    }


    return (

        <div className="auth-page">

            <div className="auth-container">

                <Link
                    to="/"
                    className="auth-logo"
                >

                    <div className="logo-mark">
                        A
                    </div>

                    <span>
                        AgentSwarm
                    </span>

                </Link>


                <div className="auth-card">

                    <div className="auth-header">

                        <p className="section-label">
                            PASSWORD RESET
                        </p>

                        <h1>
                            Create a new password
                        </h1>

                        <p>
                            Enter a new password for your
                            AgentSwarm account.
                        </p>

                    </div>


                    <form
                        className="auth-form"
                        onSubmit={handleSubmit}
                    >

                        <div className="form-group">

                            <label htmlFor="password">
                                New password
                            </label>

                            <input
                                id="password"
                                type="password"
                                placeholder="Enter new password"
                                value={password}
                                onChange={(event) =>
                                    setPassword(
                                        event.target.value
                                    )
                                }
                                minLength="8"
                                maxLength="72"
                                required
                            />

                        </div>


                        <div className="form-group">

                            <label htmlFor="confirm-password">
                                Confirm password
                            </label>

                            <input
                                id="confirm-password"
                                type="password"
                                placeholder="Confirm new password"
                                value={confirmPassword}
                                onChange={(event) =>
                                    setConfirmPassword(
                                        event.target.value
                                    )
                                }
                                minLength="8"
                                maxLength="72"
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
                                ? "Resetting..."
                                : "Reset password"
                            }

                            {!loading && (

                                <span>
                                    →
                                </span>

                            )}

                        </button>

                    </form>


                    <div className="auth-divider">
                        <span>
                            or
                        </span>
                    </div>


                    <p className="auth-switch">

                        Remember your password?{" "}

                        <Link to="/login">
                            Sign in
                        </Link>

                    </p>

                </div>


                <Link
                    to="/"
                    className="back-home"
                >
                    ← Back to AgentSwarm
                </Link>

            </div>

        </div>
    );
}


export default ResetPassword;