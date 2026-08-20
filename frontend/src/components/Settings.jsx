import { useState, useEffect } from "react";
import { Key, CheckCircle, AlertTriangle, Eye, EyeOff, Save, ShieldCheck, Sparkles, FileText, Trash2, ExternalLink, ArrowRight } from "lucide-react";
import { api } from "../lib/api";

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState({ configured: false, masked_key: "", provider: "none" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      setLoading(true);
      const res = await api.getApiKey();
      setStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    if (!apiKey.trim()) return;

    try {
      setSaving(true);
      setMessage(null);
      setError(null);
      const res = await api.saveApiKey(apiKey.trim());
      setMessage(res.message || "API Key saved successfully to .env file!");
      setStatus({ configured: true, masked_key: res.masked_key, provider: res.provider || "Gemini" });
      setApiKey("");
    } catch (err) {
      setError(err.message || "Failed to save API key.");
    } finally {
      setSaving(false);
    }
  }

  const complianceLinks = [
    {
      title: "Privacy Policy",
      path: "/privacy",
      icon: ShieldCheck,
      badge: "Meta API Compliant",
      description: "Details Meta Graph API data access (WhatsApp Cloud API, Facebook, Instagram), zero-third-party sharing, and PostgreSQL encryption standards.",
    },
    {
      title: "Terms of Service",
      path: "/terms",
      icon: FileText,
      badge: "99.9% SLA",
      description: "Enterprise SaaS service agreement covering 99.9% platform availability, acceptable use policies, Meta terms compliance, and API quota management.",
    },
    {
      title: "Data Deletion Instructions",
      path: "/data-deletion",
      icon: Trash2,
      badge: "App Review Mandatory",
      description: "Two-tier deletion mechanisms: Instant self-service credential purge via Dashboard, and an active end-user request form with 24-hour SLA.",
    },
  ];

  return (
    <div className="p-8 max-w-4xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-brand-dark flex items-center gap-2">
          AI & Workspace Settings
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Configure AI LLM keys for conversational intelligence and manage workspace compliance policies.
        </p>
      </div>

      {/* AI Key Configuration Card */}
      <div className="bg-white rounded-2xl border border-brand-border shadow-xs p-6 sm:p-8 space-y-6">
        <div>
          <h2 className="font-display text-lg font-bold text-brand-dark flex items-center gap-2">
            <Key size={18} className="text-brand-primary" />
            AI Provider & LLM Key
          </h2>
          <p className="text-xs text-text-muted mt-0.5">
            Configure Google Gemini (100% Free), Groq (Llama-3.3), or OpenAI API key to enable real-time replies across all channels.
          </p>
        </div>

        {/* Status Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-brand-bg border border-brand-border gap-3">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl ${status.configured ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {status.configured ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
            </div>
            <div>
              <div className="font-semibold text-brand-dark text-sm">
                AI Engine Status:{" "}
                {loading ? (
                  <span className="text-text-muted font-normal">Checking...</span>
                ) : status.configured ? (
                  <span className="text-emerald-600 font-semibold">Active ({status.provider || "Real AI Responses"})</span>
                ) : (
                  <span className="text-amber-600 font-semibold">Mock Mode (Not Configured)</span>
                )}
              </div>
              <div className="text-xs text-text-muted mt-0.5">
                {status.configured
                  ? `Active key: ${status.masked_key} (${status.provider})`
                  : "Currently running in fallback mock mode. Add your free Gemini or Groq key below for live replies."}
              </div>
            </div>
          </div>
          <div className="text-[11px] font-mono px-3 py-1 bg-white border border-brand-border rounded-full text-text-muted self-start sm:self-auto">
            .env target
          </div>
        </div>

        {/* Message Alert */}
        {message && (
          <div className="flex items-center gap-2 p-3.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-medium">
            <ShieldCheck size={16} className="text-emerald-600 flex-shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 p-3.5 rounded-xl bg-red-50 text-red-700 border border-red-200 text-xs font-medium">
            <AlertTriangle size={16} className="text-red-500 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-main mb-1.5">
              API Key (Google Gemini, Groq, or OpenAI)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                <Key size={16} />
              </div>
              <input
                type={showKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste Google Gemini Key (Free) or OpenAI Key..."
                className="w-full pl-9 pr-10 py-2.5 border border-brand-border rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-brand-primary-light focus:border-brand-primary font-mono text-text-main"
                required
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-brand-dark"
              >
                {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <div className="text-[11px] text-text-muted mt-2 flex flex-col gap-1">
              <span className="flex items-center gap-1.5">
                <Sparkles size={13} className="text-amber-500 flex-shrink-0" />
                <span>
                  Get a free API key from{" "}
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-primary font-semibold underline hover:text-brand-primary-hover"
                  >
                    Google AI Studio (Gemini Flash)
                  </a>{" "}
                  or{" "}
                  <a
                    href="https://console.groq.com/keys"
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-primary font-semibold underline hover:text-brand-primary-hover"
                  >
                    Groq Console (Llama-3.3)
                  </a>.
                </span>
              </span>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving || !apiKey.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand-primary hover:bg-brand-primary-hover text-white rounded-xl text-xs font-semibold shadow-2xs transition disabled:opacity-50"
          >
            <Save size={15} />
            {saving ? "Saving to .env..." : "Save AI Key to .env"}
          </button>
        </form>
      </div>

      {/* Compliance, Privacy & Meta Policies Section (Shifted from Sidebar) */}
      <div className="bg-white rounded-2xl border border-brand-border shadow-xs p-6 sm:p-8 space-y-6">
        <div>
          <h2 className="font-display text-lg font-bold text-brand-dark flex items-center gap-2">
            <ShieldCheck size={18} className="text-brand-primary" />
            Legal, Privacy & Meta Platform Compliance
          </h2>
          <p className="text-xs text-text-muted mt-0.5">
            Dedicated indexable policy documents and data deletion mechanisms required for Meta App Review and regulatory compliance.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {complianceLinks.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.path}
                href={item.path}
                target="_blank"
                rel="noopener noreferrer"
                className="group border border-brand-border hover:border-brand-primary rounded-xl p-5 bg-brand-bg/40 hover:bg-brand-primary-light/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs hover:shadow-xs"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-white border border-brand-border shadow-2xs text-brand-primary group-hover:scale-105 transition-transform">
                    <Icon size={20} />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-bold text-sm text-brand-dark group-hover:text-brand-primary transition-colors">
                        {item.title}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white border border-brand-border text-text-muted">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-xs text-text-muted leading-relaxed max-w-xl">
                      {item.description}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-xs font-semibold text-brand-primary group-hover:underline self-end sm:self-center">
                  <span>Open Page</span>
                  <ExternalLink size={13} className="opacity-80" />
                </div>
              </a>
            );
          })}
        </div>
      </div>
    </div>
  );
}
