import { useState, useEffect } from "react";
import {
  Key, CheckCircle, AlertTriangle, Eye, EyeOff, Save, ShieldCheck,
  Sparkles, FileText, Trash2, ExternalLink, Pencil, X, Plus, Loader2,
  Lock, Bell, UserCog,
} from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";

// ---------------------------------------------------------------------------
// Provider metadata (platform owner only)
// ---------------------------------------------------------------------------
const PROVIDERS = [
  {
    id: "groq",
    label: "Groq — main AI",
    model: "qwen3.8-27b + gpt-oss-120b",
    icon: "🚀",
    color: "from-orange-500 to-red-500",
    badgeColor: "bg-orange-50 text-orange-700 border-orange-200",
    description: "Understands every message and writes every reply. When you rotate the key, it is checked with Groq and used by all workspaces within 30 seconds.",
    getKeyUrl: "https://console.groq.com/keys",
    getKeyLabel: "Groq Console",
    hint: "Log in → API Keys → Create API Key",
    placeholder: "gsk_...",
  },
  {
    id: "gemini",
    label: "Google Gemini — knowledge search",
    model: "gemini-embedding-001",
    icon: "✨",
    color: "from-blue-500 to-indigo-600",
    badgeColor: "bg-blue-50 text-blue-700 border-blue-200",
    description: "Only used to index knowledge bases for meaning-based search. It never writes replies.",
    getKeyUrl: "https://aistudio.google.com/app/apikey",
    getKeyLabel: "Google AI Studio",
    hint: "Sign in with Google account → Create API key",
    placeholder: "AIza...",
  },
];

// ---------------------------------------------------------------------------
// Small shared pieces
// ---------------------------------------------------------------------------
function Notice({ msg }) {
  if (!msg) return null;
  const ok = msg.type === "success";
  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border ${
        ok ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"
      }`}
    >
      {ok ? <CheckCircle size={13} className="flex-shrink-0" /> : <AlertTriangle size={13} className="flex-shrink-0" />}
      {msg.text}
    </div>
  );
}

const inputClass =
  "w-full px-3 py-2 border border-brand-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary-light focus:border-brand-primary text-text-main";
const buttonClass =
  "flex items-center justify-center gap-1.5 px-4 py-2 bg-brand-primary hover:bg-brand-primary-hover text-white text-xs font-semibold rounded-lg transition disabled:opacity-50";

function SectionCard({ icon: Icon, title, subtitle, children }) {
  return (
    <div className="bg-white rounded-2xl border border-brand-border shadow-xs p-6 space-y-4">
      <div>
        <h2 className="font-display text-lg font-bold text-brand-dark flex items-center gap-2">
          <Icon size={18} className="text-brand-primary" />
          {title}
        </h2>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Account: change password (every user)
// ---------------------------------------------------------------------------
function ChangePasswordCard() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null);
    if (next !== confirm) {
      setMsg({ type: "error", text: "The new passwords don't match." });
      return;
    }
    setSaving(true);
    try {
      const res = await api.changePassword(current, next);
      setMsg({ type: "success", text: res.message || "Password changed." });
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Could not change the password." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard icon={Lock} title="Change password" subtitle="Use at least 8 characters.">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <input type="password" required autoComplete="current-password" value={current}
          onChange={(e) => setCurrent(e.target.value)} placeholder="Current password" className={inputClass} />
        <input type="password" required minLength={8} autoComplete="new-password" value={next}
          onChange={(e) => setNext(e.target.value)} placeholder="New password" className={inputClass} />
        <input type="password" required minLength={8} autoComplete="new-password" value={confirm}
          onChange={(e) => setConfirm(e.target.value)} placeholder="Confirm new password" className={inputClass} />
        <div className="sm:col-span-3 flex items-center gap-3">
          <button type="submit" disabled={saving} className={buttonClass}>
            {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
            {saving ? "Saving…" : "Change password"}
          </button>
          <div className="flex-1"><Notice msg={msg} /></div>
        </div>
      </form>
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Alerts: this business's own "customer wants a human" webhook (every user)
// ---------------------------------------------------------------------------
function AlertWebhookCard() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    api.getNotifications()
      .then((res) => setUrl(res.alert_webhook_url || ""))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null);
    setSaving(true);
    try {
      const res = await api.saveNotifications(url.trim());
      setUrl(res.alert_webhook_url || "");
      setMsg({ type: "success", text: res.alert_webhook_url ? "Alert webhook saved." : "Alerts turned off." });
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Could not save the webhook." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard
      icon={Bell}
      title="Alerts"
      subtitle="When a customer asks to talk to a person, we post an alert to this webhook. Works with Slack incoming webhooks, Discord webhooks, Zapier or Make. Leave it empty to turn alerts off."
    >
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="url" value={url} disabled={loading} onChange={(e) => setUrl(e.target.value)}
          placeholder="https://hooks.slack.com/services/..." className={`${inputClass} font-mono text-xs`} />
        <button type="submit" disabled={saving || loading} className={buttonClass}>
          {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
          {saving ? "Saving…" : "Save"}
        </button>
      </form>
      <Notice msg={msg} />
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// Platform owner: reset a client's password
// ---------------------------------------------------------------------------
function ResetClientPasswordCard() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null);
    setSaving(true);
    try {
      const res = await api.adminResetPassword(email.trim(), password);
      setMsg({ type: "success", text: `${res.message} Share the temporary password with them privately.` });
      setEmail("");
      setPassword("");
    } catch (err) {
      setMsg({ type: "error", text: err.message || "Could not reset the password." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <SectionCard
      icon={UserCog}
      title="Reset a client's password"
      subtitle="For clients who forgot their password: set a temporary one, send it to them privately, and ask them to change it under Settings."
    >
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          placeholder="client@business.com" className={inputClass} />
        <input type="text" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder="Temporary password (8+ characters)" className={inputClass} autoComplete="off" />
        <button type="submit" disabled={saving} className={buttonClass}>
          {saving ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
          {saving ? "Resetting…" : "Reset"}
        </button>
      </form>
      <Notice msg={msg} />
    </SectionCard>
  );
}

// ---------------------------------------------------------------------------
// ProviderCard component
// ---------------------------------------------------------------------------
function ProviderCard({ provider, keyData, onSaved, onDeleted }) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [inputKey, setInputKey] = useState("");
  const [showInput, setShowInput] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [cardMsg, setCardMsg] = useState(null);

  const isConfigured = keyData?.configured ?? false;

  function flash(type, text) {
    setCardMsg({ type, text });
    setTimeout(() => setCardMsg(null), 3500);
  }

  async function handleSave(e) {
    e.preventDefault();
    if (!inputKey.trim()) return;
    setSaving(true);
    try {
      const res = await api.saveProviderKey(provider.id, inputKey.trim());
      onSaved(provider.id, res);
      setEditing(false);
      setInputKey("");
      setShowInput(false);
      flash("success", res.message || "API key saved!");
    } catch (err) {
      flash("error", err.message || "Failed to save key.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      const res = await api.deleteProviderKey(provider.id);
      onDeleted(provider.id, res);
      setConfirmDelete(false);
      flash("success", res.message || "API key removed.");
    } catch (err) {
      flash("error", err.message || "Failed to delete key.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-brand-border shadow-xs overflow-hidden flex flex-col">
      {/* Gradient top strip */}
      <div className={`h-1.5 w-full bg-gradient-to-r ${provider.color}`} />

      <div className="p-5 flex flex-col gap-4 flex-1">
        {/* Top row: icon + name + status */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="text-2xl leading-none select-none">{provider.icon}</div>
            <div>
              <div className="font-display font-bold text-sm text-brand-dark leading-tight">
                {provider.label}
              </div>
              <div className="text-[11px] font-mono text-text-muted">{provider.model}</div>
            </div>
          </div>
          {isConfigured ? (
            <span className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${provider.badgeColor}`}>
              <CheckCircle size={10} />
              Active
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border bg-amber-50 text-amber-700 border-amber-200">
              <AlertTriangle size={10} />
              Not set
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-[11px] text-text-muted leading-relaxed">{provider.description}</p>

        {/* Masked key display */}
        {isConfigured && !editing && (
          <div className="flex items-center gap-2 px-3 py-2 bg-brand-bg border border-brand-border rounded-xl">
            <Key size={13} className="text-text-muted flex-shrink-0" />
            <span className="font-mono text-[11px] text-text-main tracking-wider flex-1">
              {keyData.masked_key}
            </span>
          </div>
        )}

        {/* Card flash message */}
        {cardMsg && (
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-medium border ${
              cardMsg.type === "success"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-red-50 text-red-700 border-red-200"
            }`}
          >
            {cardMsg.type === "success" ? (
              <CheckCircle size={12} className="flex-shrink-0" />
            ) : (
              <AlertTriangle size={12} className="flex-shrink-0" />
            )}
            {cardMsg.text}
          </div>
        )}

        {/* Delete confirmation */}
        {confirmDelete && (
          <div className="flex flex-col gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-[11px] text-red-700 font-medium">
              Remove this key? Features that use it stop working for every workspace until a new key is added.
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-red-600 hover:bg-red-700 text-white text-[11px] font-semibold rounded-lg transition disabled:opacity-50"
              >
                {deleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                {deleting ? "Removing…" : "Yes, Remove"}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="flex-1 py-1.5 bg-white hover:bg-brand-bg text-text-main text-[11px] font-semibold rounded-lg border border-brand-border transition"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Inline edit form */}
        {editing && (
          <form onSubmit={handleSave} className="flex flex-col gap-2">
            <label className="text-[11px] font-semibold text-text-main">
              {isConfigured ? "Replace API Key" : "Add API Key"}
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
                <Key size={13} />
              </div>
              <input
                autoFocus
                type={showInput ? "text" : "password"}
                value={inputKey}
                onChange={(e) => setInputKey(e.target.value)}
                placeholder={provider.placeholder}
                className="w-full pl-8 pr-9 py-2 border border-brand-border rounded-xl text-[11px] focus:outline-none focus:ring-2 focus:ring-brand-primary-light focus:border-brand-primary font-mono text-text-main"
                required
              />
              <button
                type="button"
                onClick={() => setShowInput(!showInput)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-brand-dark"
              >
                {showInput ? <EyeOff size={13} /> : <Eye size={13} />}
              </button>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving || !inputKey.trim()}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-brand-primary hover:bg-brand-primary-hover text-white text-[11px] font-semibold rounded-lg transition disabled:opacity-50"
              >
                {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                {saving ? "Saving…" : "Save Key"}
              </button>
              <button
                type="button"
                onClick={() => { setEditing(false); setInputKey(""); setShowInput(false); }}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-white hover:bg-brand-bg text-text-main text-[11px] font-semibold rounded-lg border border-brand-border transition"
              >
                <X size={12} />
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Action row */}
        {!editing && !confirmDelete && (
          <div className="flex items-center gap-2 mt-auto pt-1">
            {isConfigured ? (
              <>
                <button
                  onClick={() => { setEditing(true); setConfirmDelete(false); }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-bg hover:bg-brand-primary-light border border-brand-border hover:border-brand-primary text-text-main hover:text-brand-primary text-[11px] font-semibold rounded-lg transition"
                >
                  <Pencil size={11} />
                  Edit
                </button>
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 hover:bg-red-100 border border-red-200 text-red-600 text-[11px] font-semibold rounded-lg transition"
                >
                  <Trash2 size={11} />
                  Delete
                </button>
              </>
            ) : (
              <button
                onClick={() => { setEditing(true); setConfirmDelete(false); }}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-primary hover:bg-brand-primary-hover text-white text-[11px] font-semibold rounded-lg transition"
              >
                <Plus size={11} />
                Add Key
              </button>
            )}

            <a
              href={provider.getKeyUrl}
              target="_blank"
              rel="noreferrer"
              title={provider.hint}
              className="ml-auto flex items-center gap-1 text-[11px] font-semibold text-brand-primary hover:text-brand-primary-hover hover:underline"
            >
              Get API Key
              <ExternalLink size={11} className="opacity-80" />
            </a>
          </div>
        )}

        {/* Provider console hint */}
        <div className="flex items-start gap-1.5 text-[10px] text-text-muted">
          <Sparkles size={11} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <span>
            <a
              href={provider.getKeyUrl}
              target="_blank"
              rel="noreferrer"
              className="text-brand-primary font-semibold hover:underline"
            >
              {provider.getKeyLabel}
            </a>
            {" — "}
            {provider.hint}
          </span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Settings page
// ---------------------------------------------------------------------------
export default function Settings() {
  const { user } = useAuth();
  const isOwner = Boolean(user?.is_platform_admin);
  const [keysData, setKeysData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOwner) fetchAllKeys();
    else setLoading(false);
  }, [isOwner]);

  async function fetchAllKeys() {
    try {
      setLoading(true);
      const res = await api.getAllApiKeys();
      setKeysData(res);
    } catch (err) {
      console.error("Failed to fetch API keys:", err);
    } finally {
      setLoading(false);
    }
  }

  function handleSaved(providerId, res) {
    setKeysData((prev) => ({
      ...prev,
      [providerId]: {
        ...(prev[providerId] || {}),
        configured: res.configured,
        masked_key: res.masked_key,
      },
    }));
  }

  function handleDeleted(providerId) {
    setKeysData((prev) => ({
      ...prev,
      [providerId]: {
        ...(prev[providerId] || {}),
        configured: false,
        masked_key: "",
      },
    }));
  }

  const configuredCount = PROVIDERS.filter((p) => keysData[p.id]?.configured).length;

  const complianceLinks = [
    {
      title: "Privacy Policy",
      path: "/privacy",
      icon: ShieldCheck,
      badge: "Meta API Compliant",
      description:
        "Details Meta Graph API data access (WhatsApp Cloud API, Facebook, Instagram), zero-third-party sharing, and PostgreSQL encryption standards.",
    },
    {
      title: "Terms of Service",
      path: "/terms",
      icon: FileText,
      badge: "99.9% SLA",
      description:
        "Enterprise SaaS service agreement covering 99.9% platform availability, acceptable use policies, Meta terms compliance, and API quota management.",
    },
    {
      title: "Data Deletion Instructions",
      path: "/data-deletion",
      icon: Trash2,
      badge: "App Review Mandatory",
      description:
        "Two-tier deletion mechanisms: Instant self-service credential purge via Dashboard, and an active end-user request form with 24-hour SLA.",
    },
  ];

  return (
    <div className="p-8 max-w-5xl space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-brand-dark flex items-center gap-2">
          Settings
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Manage your account, alerts and compliance pages.
        </p>
      </div>

      <ChangePasswordCard />
      <AlertWebhookCard />

      {/* Platform owner only: shared AI keys and client support */}
      {isOwner && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key size={18} className="text-brand-primary" />
              <h2 className="font-display text-lg font-bold text-brand-dark">
                Platform AI keys
              </h2>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-bg border border-brand-border text-text-muted">
                Owner only
              </span>
            </div>
            {!loading && (
              <div
                className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border ${
                  configuredCount === PROVIDERS.length
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-amber-50 text-amber-700 border-amber-200"
                }`}
              >
                {configuredCount === PROVIDERS.length ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
                {configuredCount}/{PROVIDERS.length} keys configured
              </div>
            )}
          </div>

          <p className="text-xs text-text-muted -mt-1">
            These keys are shared by every workspace on the platform. Only you can see or change them.
          </p>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {PROVIDERS.map((p) => (
                <div key={p.id} className="bg-white rounded-2xl border border-brand-border h-52 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {PROVIDERS.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  keyData={keysData[provider.id]}
                  onSaved={handleSaved}
                  onDeleted={handleDeleted}
                />
              ))}
            </div>
          )}

          <ResetClientPasswordCard />
        </div>
      )}

      {/* Compliance Section */}
      <div className="bg-white rounded-2xl border border-brand-border shadow-xs p-6 sm:p-8 space-y-6">
        <div>
          <h2 className="font-display text-lg font-bold text-brand-dark flex items-center gap-2">
            <ShieldCheck size={18} className="text-brand-primary" />
            Legal, Privacy &amp; Meta Platform Compliance
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

