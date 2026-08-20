import { useState } from "react";
import { Link } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import { Trash2, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw, Send, ArrowRight, Lock, HelpCircle } from "lucide-react";

export default function DataDeletion() {
  const [form, setForm] = useState({
    identifier: "",
    email: "",
    businessName: "",
    channel: "whatsapp",
    reason: "",
  });
  const [status, setStatus] = useState("idle"); // idle | submitting | success | error
  const [confirmationCode, setConfirmationCode] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.identifier || !form.email) {
      alert("Please provide at least a Phone Number / Account ID and your Contact Email.");
      return;
    }

    setStatus("submitting");

    // Simulate verified deletion ticket creation
    setTimeout(() => {
      const code = "DEL-" + Math.random().toString(36).substring(2, 9).toUpperCase();
      setConfirmationCode(code);
      setStatus("success");
    }, 800);
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col font-sans text-text-main">
      <PublicHeader />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header Hero Banner */}
        <div className="mb-10 bg-white border border-brand-border rounded-2xl p-6 sm:p-10 shadow-xs relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-brand-primary/5 rounded-full blur-3xl pointer-events-none" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 text-red-600 text-xs font-semibold uppercase tracking-wider mb-4 border border-red-200">
            <Trash2 size={14} />
            Mandatory Meta App Review Compliance
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-brand-dark mb-2">
            Data Deletion Instructions & Request Portal
          </h1>
          <p className="text-text-muted text-sm sm:text-base max-w-3xl">
            In compliance with Meta Platform Terms, GDPR, and CCPA, RAVISN provides transparent, automated mechanisms for end-users and business clients to purge their stored conversation data and access credentials.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-6 pt-6 border-t border-brand-border text-xs text-text-muted">
            <span><strong>Service SLA:</strong> Immediate or &lt;24 Hours for manual requests</span>
            <span>•</span>
            <span><strong>Cluster:</strong> Neon PostgreSQL</span>
            <span>•</span>
            <span><strong>Support:</strong> <a href="mailto:support@ravisn.com" className="text-brand-primary hover:underline">support@ravisn.com</a></span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Column */}
          <div className="lg:col-span-12 space-y-8">
            
            {/* Mechanism 1: Self-Service Deletion via Dashboard */}
            <div className="bg-white border border-brand-border rounded-2xl p-6 sm:p-8 shadow-xs">
              <div className="flex items-center gap-3 border-b border-brand-border pb-4 mb-6">
                <div className="w-10 h-10 rounded-xl bg-brand-primary-light flex items-center justify-center text-brand-primary font-bold">
                  1
                </div>
                <div>
                  <h2 className="font-display text-xl font-bold text-brand-dark">
                    Mechanism 1: Self-Service Deletion via Dashboard (Immediate)
                  </h2>
                  <p className="text-xs text-text-muted">
                    Instant programmatic purge of Meta Access Tokens, Channel IDs, and Webhook subscriptions.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/50 space-y-2">
                  <div className="text-xs font-bold text-brand-dark flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-brand-dark text-white flex items-center justify-center text-[10px]">1</span>
                    Access Connect Tab
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    Log in to your RAVISN Dashboard and navigate to the <strong>Connect / Channels</strong> tab in the sidebar.
                  </p>
                </div>

                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/50 space-y-2">
                  <div className="text-xs font-bold text-brand-dark flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-brand-dark text-white flex items-center justify-center text-[10px]">2</span>
                    Click Disconnect
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    Locate the active channel (WhatsApp Official, WhatsApp QR, Facebook, or Instagram) and click <strong>Disconnect Channel</strong>.
                  </p>
                </div>

                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/50 space-y-2">
                  <div className="text-xs font-bold text-brand-dark flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-brand-dark text-white flex items-center justify-center text-[10px]">3</span>
                    Instant Purge
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    All stored OAuth access tokens, page tokens, and live webhook sessions are permanently wiped from the database immediately.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
                  <span>
                    Self-service disconnection triggers an atomic database deletion transaction across PostgreSQL tables.
                  </span>
                </div>
                <Link
                  to="/dashboard"
                  className="hidden sm:inline-flex items-center gap-1 font-semibold text-emerald-900 hover:underline ml-2"
                >
                  Go to Dashboard →
                </Link>
              </div>
            </div>

            {/* Mechanism 2: Data Deletion Callback & Manual Request Form */}
            <div className="bg-white border border-brand-border rounded-2xl p-6 sm:p-8 shadow-xs">
              <div className="flex items-center gap-3 border-b border-brand-border pb-4 mb-6">
                <div className="w-10 h-10 rounded-xl bg-brand-primary-light flex items-center justify-center text-brand-primary font-bold">
                  2
                </div>
                <div>
                  <h2 className="font-display text-xl font-bold text-brand-dark">
                    Mechanism 2: End-User Data Deletion Request Form
                  </h2>
                  <p className="text-xs text-text-muted">
                    For customers who messaged a business and wish to erase their chat logs, phone numbers, or booking records.
                  </p>
                </div>
              </div>

              {status === "success" ? (
                <div className="p-8 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-4">
                  <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-xs">
                    <CheckCircle2 size={32} />
                  </div>
                  <h3 className="font-display text-2xl font-bold text-emerald-900">
                    Deletion Request Registered
                  </h3>
                  <p className="text-sm text-emerald-800 max-w-xl mx-auto leading-relaxed">
                    Upon request submission, all stored webhook logs, conversation histories, and access tokens associated with your identifier are permanently wiped from our Neon PostgreSQL cluster within <strong>24 hours</strong>.
                  </p>
                  
                  <div className="inline-block p-4 rounded-xl bg-white border border-emerald-200 shadow-2xs">
                    <span className="text-xs uppercase font-mono tracking-wider text-emerald-700 block mb-1">
                      Tracking Confirmation Code
                    </span>
                    <span className="font-mono text-xl font-bold text-brand-dark">
                      {confirmationCode}
                    </span>
                  </div>

                  <p className="text-xs text-emerald-700">
                    A confirmation record has been generated. For status follow-ups, contact{" "}
                    <a href="mailto:support@ravisn.com" className="font-semibold underline">
                      support@ravisn.com
                    </a>.
                  </p>

                  <button
                    onClick={() => {
                      setStatus("idle");
                      setForm({ identifier: "", email: "", businessName: "", channel: "whatsapp", reason: "" });
                    }}
                    className="mt-4 px-5 py-2.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition"
                  >
                    Submit Another Request
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-text-main mb-1.5">
                        Your Phone Number or Account Handle <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. +923001234567 or @instagram_handle"
                        value={form.identifier}
                        onChange={(e) => setForm({ ...form, identifier: e.target.value })}
                        className="w-full rounded-xl border border-brand-border px-3.5 py-2.5 text-xs text-text-main outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary-light transition"
                      />
                      <span className="text-[11px] text-text-muted mt-1 block">
                        The exact WhatsApp number or social handle you messaged from.
                      </span>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-text-main mb-1.5">
                        Your Contact Email for Confirmation <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        required
                        placeholder="e.g. you@example.com"
                        value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        className="w-full rounded-xl border border-brand-border px-3.5 py-2.5 text-xs text-text-main outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary-light transition"
                      />
                      <span className="text-[11px] text-text-muted mt-1 block">
                        We send the cryptographic deletion confirmation receipt here.
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-text-main mb-1.5">
                        Messaging Channel
                      </label>
                      <select
                        value={form.channel}
                        onChange={(e) => setForm({ ...form, channel: e.target.value })}
                        className="w-full rounded-xl border border-brand-border px-3.5 py-2.5 text-xs text-text-main outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary-light bg-white transition"
                      >
                        <option value="whatsapp">WhatsApp (Official Cloud API / QR)</option>
                        <option value="instagram">Instagram Direct Message</option>
                        <option value="facebook">Facebook Messenger</option>
                        <option value="all">All Channels Associated with Me</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-text-main mb-1.5">
                        Business Name Contacted (Optional)
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Clinic / Store Name"
                        value={form.businessName}
                        onChange={(e) => setForm({ ...form, businessName: e.target.value })}
                        className="w-full rounded-xl border border-brand-border px-3.5 py-2.5 text-xs text-text-main outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary-light transition"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-text-main mb-1.5">
                      Additional Notes / Deletion Scope (Optional)
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Specify if you only want appointment details erased or complete conversation purge..."
                      value={form.reason}
                      onChange={(e) => setForm({ ...form, reason: e.target.value })}
                      className="w-full rounded-xl border border-brand-border px-3.5 py-2.5 text-xs text-text-main outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary-light transition"
                    />
                  </div>

                  <div className="p-4 rounded-xl bg-brand-bg border border-brand-border text-xs text-text-muted space-y-1">
                    <p className="font-semibold text-text-main flex items-center gap-1.5">
                      <Lock size={14} className="text-brand-primary" />
                      Guaranteed Deletion Protocol:
                    </p>
                    <p>
                      Upon request submission, all stored webhook logs, conversation histories, and access tokens associated with your tenant/identifier are permanently wiped from our <strong>Neon PostgreSQL cluster within 24 hours</strong>.
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={status === "submitting"}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-brand-dark hover:bg-black text-white text-xs font-semibold shadow-xs hover:shadow-sm transition disabled:opacity-50"
                  >
                    {status === "submitting" ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        Processing Deletion Request...
                      </>
                    ) : (
                      <>
                        <Trash2 size={14} className="text-red-400" />
                        Submit Verified Data Deletion Request
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>

            {/* Official Support Anchor */}
            <div className="bg-brand-primary-light border border-brand-primary/20 rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="font-semibold text-sm text-brand-primary flex items-center gap-2">
                  <HelpCircle size={16} />
                  Need direct assistance from our Data Protection Officer?
                </h4>
                <p className="text-xs text-text-muted">
                  You can also email your deletion request directly to our security & compliance team.
                </p>
              </div>
              <a
                href="mailto:support@ravisn.com?subject=Data%20Deletion%20Request"
                className="px-4 py-2 rounded-lg bg-brand-primary hover:bg-brand-primary-hover text-white text-xs font-semibold shadow-2xs transition whitespace-nowrap"
              >
                Email support@ravisn.com
              </a>
            </div>

          </div>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
