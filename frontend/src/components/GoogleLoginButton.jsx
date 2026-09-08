import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_URL } from "../config";

export default function GoogleLoginButton({ onError }) {
    const navigate = useNavigate();
    const buttonRef = useRef(null);
    const [isConfigured, setIsConfigured] = useState(false);
    const [loading, setLoading] = useState(false);

    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    async function handleCredentialResponse(response) {
        if (!response || !response.credential) {
            if (onError) onError("No credential received from Google.");
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/auth/google`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    id_token: response.credential
                })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Google authentication failed.");
            }

            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("user_email", data.email);
            if (data.name) localStorage.setItem("user_name", data.name);
            if (data.avatar_url) localStorage.setItem("user_avatar", data.avatar_url);

            navigate("/dashboard");
        } catch (err) {
            if (onError) onError(err.message || "Failed to sign in with Google.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        const isRealClientId = googleClientId && 
            googleClientId !== "placeholder" && 
            googleClientId !== "optional" && 
            googleClientId.trim().length > 10;

        if (!isRealClientId) {
            setIsConfigured(false);
            return;
        }

        setIsConfigured(true);

        let isMounted = true;
        let retryCount = 0;

        const checkGoogleScript = () => {
            if (!isMounted) return;

            try {
                if (window.google?.accounts?.id && buttonRef.current) {
                    window.google.accounts.id.initialize({
                        client_id: googleClientId,
                        callback: handleCredentialResponse,
                        auto_select: false
                    });

                    // Clear container before rendering
                    buttonRef.current.innerHTML = "";

                    window.google.accounts.id.renderButton(buttonRef.current, {
                        theme: "outline",
                        size: "large",
                        type: "standard",
                        text: "signin_with",
                        shape: "rectangular",
                        logo_alignment: "left",
                        width: 340
                    });
                } else if (retryCount < 15) {
                    retryCount++;
                    setTimeout(checkGoogleScript, 300);
                }
            } catch (err) {
                console.warn("Google Sign-In initialization error:", err);
                if (isMounted) setIsConfigured(false);
            }
        };

        checkGoogleScript();

        return () => {
            isMounted = false;
        };
    }, [googleClientId]);

    const handleUnconfiguredClick = () => {
        if (onError) {
            onError(
                "Google Sign-In is ready! To enable it live, add your VITE_GOOGLE_CLIENT_ID from Google Cloud Console to your frontend environment."
            );
        } else {
            alert(
                "Google Sign-In is ready! Set VITE_GOOGLE_CLIENT_ID in your .env or hosting settings to link your Google OAuth credentials."
            );
        }
    };

    return (
        <div className="google-auth-wrapper" style={{ width: "100%", display: "flex", justifyContent: "center", margin: "14px 0" }}>
            {isConfigured ? (
                <div ref={buttonRef} style={{ width: "100%", minHeight: "44px", display: "flex", justifyContent: "center" }}>
                    {loading && <p style={{ fontSize: "0.85rem", color: "#888" }}>Connecting to Google...</p>}
                </div>
            ) : (
                <button
                    type="button"
                    onClick={handleUnconfiguredClick}
                    className="google-signin-fallback-btn"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "12px",
                        width: "100%",
                        padding: "11px 16px",
                        backgroundColor: "#ffffff",
                        color: "#3c4043",
                        border: "1px solid #dadce0",
                        borderRadius: "8px",
                        fontSize: "0.95rem",
                        fontWeight: 500,
                        cursor: "pointer",
                        transition: "background-color 0.2s, box-shadow 0.2s",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.08)"
                    }}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                    </svg>
                    <span>Sign in with Google</span>
                </button>
            )}
        </div>
    );
}
