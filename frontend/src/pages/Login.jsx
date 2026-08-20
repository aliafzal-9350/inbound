import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import RavisnLogo from "../components/RavisnLogo";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Forgot password modal state
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetSuccess, setResetSuccess] = useState("");
  const [resetError, setResetError] = useState("");
  const [resetLoading, setResetLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(e) {
    e.preventDefault();
    setResetError("");
    setResetSuccess("");
    setResetLoading(true);
    try {
      const res = await api.post("/auth/reset-password", {
        email: forgotEmail,
        new_password: newPassword,
      });
      setResetSuccess("Password reset successfully! You can now log in with your new password.");
      setTimeout(() => {
        setShowForgotModal(false);
        setResetSuccess("");
        setEmail(forgotEmail);
      }, 2000);
    } catch (err) {
      setResetError(err.message);
    } finally {
      setResetLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="hidden md:flex md:w-1/2 bg-brand-dark text-white flex-col justify-between p-12 border-r border-brand-border-dark">
        <div>
          <RavisnLogo variant="light" size="lg" />
        </div>
        <div>
          <p className="font-display text-3xl leading-snug max-w-sm font-bold">
            One inbox for every customer conversation.
          </p>
          <p className="text-white/60 mt-4 max-w-sm text-sm leading-relaxed">
            WhatsApp, Instagram, and Facebook Messenger, answered autonomously with strict knowledge-base precision.
          </p>
        </div>
        <div className="text-white/40 text-xs font-mono">RAVISN ENTERPRISE AGENT</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-brand-bg">
        <div className="w-full max-w-sm">
          <div className="md:hidden mb-6">
            <RavisnLogo variant="dark" size="md" />
          </div>
          <h1 className="font-display text-2xl font-bold mb-1 text-brand-dark">Log in</h1>
          <p className="text-text-muted text-xs mb-8">Welcome back to your workspace.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="you@business.com"
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium" htmlFor="password">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setResetEmail(email);
                    setShowForgotModal(true);
                  }}
                  className="text-xs text-accent hover:underline font-medium"
                >
                  Forgot password?
                </button>
              </div>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-accent text-white font-medium py-2.5 hover:opacity-90 transition disabled:opacity-60"
            >
              {loading ? "Logging in…" : "Log in"}
            </button>
          </form>

          <p className="text-sm text-ink-muted mt-6">
            New to RAVISN?{" "}
            <Link to="/signup" className="text-accent font-medium hover:underline">
              Create an account
            </Link>
          </p>

          <p className="text-xs text-ink-muted mt-4 flex gap-3 flex-wrap">
            <Link to="/privacy" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Privacy Policy
            </Link>
            <span>•</span>
            <Link to="/terms" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Terms & Conditions
            </Link>
            <span>•</span>
            <Link to="/data-deletion" target="_blank" rel="noopener noreferrer" className="hover:underline">
              Data Deletion
            </Link>
          </p>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h2 className="text-xl font-semibold mb-2">Reset Password</h2>
            <p className="text-sm text-ink-muted mb-4">
              Enter your email and a new password to update your login credentials.
            </p>

            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="w-full rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-accent"
                  placeholder="you@business.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">New Password</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-accent"
                  placeholder="At least 6 characters"
                />
              </div>

              {resetError && <p className="text-xs text-red-600">{resetError}</p>}
              {resetMessage && <p className="text-xs text-green-600 font-medium">{resetMessage}</p>}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowForgotModal(false)}
                  className="flex-1 py-2 rounded-lg border border-line text-sm font-medium hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resetLoading}
                  className="flex-1 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:opacity-90 transition disabled:opacity-60"
                >
                  {resetLoading ? "Updating…" : "Update Password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
