import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import RavisnLogo from "../components/RavisnLogo";

function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [businessName, setBusinessName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugManual, setSlugManual] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleNameChange(e) {
    const val = e.target.value;
    setBusinessName(val);
    if (!slugManual) {
      setSlug(slugify(val));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await signup(businessName, slug, email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
            Set up your business in a couple of minutes.
          </p>
          <p className="text-white/60 mt-4 max-w-sm text-sm leading-relaxed">
            Connect WhatsApp, Instagram and Facebook once you're in.
          </p>
        </div>
        <div className="text-white/40 text-xs font-mono">RAVISN ENTERPRISE AGENT</div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-brand-bg">
        <div className="w-full max-w-sm">
          <div className="md:hidden mb-6">
            <RavisnLogo variant="dark" size="md" />
          </div>
          <h1 className="font-display text-2xl font-bold mb-1 text-brand-dark">Create your account</h1>
          <p className="text-text-muted text-xs mb-8">Free to set up.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5" htmlFor="business">
                Business name
              </label>
              <input
                id="business"
                required
                value={businessName}
                onChange={(e) => handleBusinessName(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="Bright Smile Clinic"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5" htmlFor="slug">
                Workspace url
              </label>
              <input
                id="slug"
                required
                value={slug}
                onChange={(e) => {
                  setSlug(slugify(e.target.value));
                  setSlugEdited(true);
                }}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition font-mono text-sm"
                placeholder="bright-smile-clinic"
              />
            </div>
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
              <label className="block text-sm font-medium mb-1.5" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-line px-3.5 py-2.5 outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft transition"
                placeholder="At least 8 characters"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-accent text-white font-medium py-2.5 hover:opacity-90 transition disabled:opacity-60"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-sm text-ink-muted mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-accent font-medium hover:underline">
              Log in
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
    </div>
  );
}
