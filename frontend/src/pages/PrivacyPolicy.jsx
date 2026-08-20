import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import { ShieldCheck, Lock, Database, EyeOff, Share2, Server, HelpCircle, Mail, CheckCircle2 } from "lucide-react";

export default function PrivacyPolicy() {
  const [activeSection, setActiveSection] = useState("overview");

  const sections = [
    { id: "overview", label: "1. Overview & Scope" },
    { id: "meta-api", label: "2. Meta API Data Access" },
    { id: "data-collected", label: "3. What Data We Collect & Store" },
    { id: "zero-sharing", label: "4. Zero-Third-Party Sharing" },
    { id: "encryption", label: "5. Storage & Encryption Standards" },
    { id: "retention", label: "6. Data Retention & Deletion" },
    { id: "user-rights", label: "7. Your Rights & Controls" },
    { id: "contact", label: "8. Contact Information" },
  ];

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 120;
      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const top = element.offsetTop;
          const height = element.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveSection(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollTo = (id) => {
    const element = document.getElementById(id);
    if (element) {
      window.scrollTo({
        top: element.offsetTop - 90,
        behavior: "smooth",
      });
    }
  };

  return (
    <div className="min-h-screen bg-brand-bg flex flex-col font-sans text-text-main">
      <PublicHeader />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10">
        {/* Header Hero Banner */}
        <div className="mb-10 bg-white border border-brand-border rounded-2xl p-6 sm:p-10 shadow-xs relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-brand-primary/5 rounded-full blur-3xl pointer-events-none" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-primary-light text-brand-primary text-xs font-semibold uppercase tracking-wider mb-4">
            <ShieldCheck size={14} />
            Official Meta-Compliant Privacy Policy
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-brand-dark mb-2">
            RAVISN Privacy Policy
          </h1>
          <p className="text-text-muted text-sm sm:text-base max-w-3xl">
            This document outlines how RAVISN collects, processes, encrypts, and protects conversation data across Meta Platforms (WhatsApp Cloud API, Facebook Messenger, Instagram Direct) and Web channels.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-6 pt-6 border-t border-brand-border text-xs text-text-muted">
            <span><strong>Effective Date:</strong> January 1, 2026</span>
            <span>•</span>
            <span><strong>Last Updated:</strong> August 20, 2026</span>
            <span>•</span>
            <span><strong>Applicability:</strong> Global & Meta Platform Terms v20.0+</span>
          </div>
        </div>

        {/* Content Layout with Sticky Sidebar TOC */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Desktop Sticky Table of Contents */}
          <aside className="hidden lg:block lg:col-span-4 sticky top-24">
            <div className="bg-white border border-brand-border rounded-xl p-5 shadow-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted mb-3">
                Table of Contents
              </h3>
              <nav className="space-y-1">
                {sections.map((sec) => (
                  <button
                    key={sec.id}
                    onClick={() => scrollTo(sec.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      activeSection === sec.id
                        ? "bg-brand-primary-light text-brand-primary font-semibold shadow-2xs"
                        : "text-text-muted hover:text-brand-dark hover:bg-gray-50"
                    }`}
                  >
                    {sec.label}
                  </button>
                ))}
              </nav>

              <div className="mt-6 pt-5 border-t border-brand-border">
                <Link
                  to="/data-deletion"
                  className="flex items-center justify-between text-xs font-semibold text-brand-primary hover:underline"
                >
                  <span>Need to delete your data?</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          </aside>

          {/* Main Legal Document Content */}
          <div className="lg:col-span-8 bg-white border border-brand-border rounded-2xl p-6 sm:p-10 shadow-xs space-y-10">
            {/* 1. Overview */}
            <section id="overview" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <ShieldCheck className="text-brand-primary" size={22} />
                <h2>1. Overview & Scope</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                RAVISN ("we," "us," "our") provides intelligent conversational AI middleware and automation technology that businesses ("Business Tenants" or "Clients") use to communicate with their end customers over messaging platforms including WhatsApp, Facebook Messenger, Instagram Direct, and web chat.
              </p>
              <p className="text-text-muted text-sm leading-relaxed">
                When an end user messages a business powered by RAVISN, RAVISN acts strictly as a <strong>Data Processor</strong> on behalf of that Business Tenant (the <strong>Data Controller</strong>). We process incoming messages exclusively to generate instant, grounded replies from the business's own verified Knowledge Base and facilitate customer support interactions.
              </p>
            </section>

            {/* 2. Meta API Data Access */}
            <section id="meta-api" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Share2 className="text-brand-primary" size={22} />
                <h2>2. Meta API Data Access & Integration</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                RAVISN integrates directly with Meta Graph APIs in strict compliance with the <strong>Meta Platform Terms</strong> and <strong>Developer Policies</strong>:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/60 space-y-1.5">
                  <span className="text-xs font-bold text-emerald-600">WhatsApp Cloud API</span>
                  <p className="text-[11px] text-text-muted">
                    Ingests verified webhook payloads for incoming messages, delivery statuses, and customer inquiries.
                  </p>
                </div>
                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/60 space-y-1.5">
                  <span className="text-xs font-bold text-blue-600">Facebook Messenger</span>
                  <p className="text-[11px] text-text-muted">
                    Processes Page-Scoped User IDs (PSIDs) to deliver automated customer service responses.
                  </p>
                </div>
                <div className="border border-brand-border rounded-xl p-4 bg-brand-bg/60 space-y-1.5">
                  <span className="text-xs font-bold text-pink-600">Instagram Graph API</span>
                  <p className="text-[11px] text-text-muted">
                    Receives Instagram-Scoped User IDs (IGSIDs) for direct messaging and booking inquiries.
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-brand-primary-light border border-brand-primary/20 text-xs text-brand-primary font-medium flex items-start gap-2.5">
                <CheckCircle2 size={16} className="flex-shrink-0 mt-0.5" />
                <span>
                  All Meta Webhooks are verified using cryptographic SHA256 HMAC signature verification with the tenant's configured <code className="bg-white/80 px-1 py-0.5 rounded font-mono">META_APP_SECRET</code>. Unsigned requests are discarded immediately.
                </span>
              </div>
            </section>

            {/* 3. What Data We Collect & Store */}
            <section id="data-collected" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Database className="text-brand-primary" size={22} />
                <h2>3. What Data We Collect & Store</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                We only collect and store data strictly necessary for fulfilling customer inquiries and appointment bookings:
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border border-brand-border rounded-xl overflow-hidden">
                  <thead className="bg-brand-bg text-text-main font-semibold border-b border-brand-border">
                    <tr>
                      <th className="p-3">Data Element</th>
                      <th className="p-3">Purpose</th>
                      <th className="p-3">Retention Basis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border text-text-muted">
                    <tr>
                      <td className="p-3 font-medium text-text-main">Platform Identifier (Phone / PSID / IGSID)</td>
                      <td className="p-3">Routing replies to the correct customer conversation thread</td>
                      <td className="p-3">Duration of business customer support relationship</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-text-main">Message Content & Timestamps</td>
                      <td className="p-3">Generating contextual AI replies and maintaining conversation history</td>
                      <td className="p-3">Tenant support audit log</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-text-main">Customer Lead / Booking Details</td>
                      <td className="p-3">Name, contact info, and appointment slot requested by customer</td>
                      <td className="p-3">Business appointment schedule fulfillment</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-medium text-text-main">Tenant Knowledge Base</td>
                      <td className="p-3">Grounding AI responses in company facts, pricing, and services</td>
                      <td className="p-3">Controlled directly by Business Tenant</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* 4. Zero-Third-Party Sharing */}
            <section id="zero-sharing" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <EyeOff className="text-brand-primary" size={22} />
                <h2>4. Zero-Third-Party Sharing & No Ad Targeting</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                RAVISN operates on a strict privacy model:
              </p>
              <ul className="space-y-2 text-xs text-text-muted list-disc list-inside">
                <li><strong className="text-text-main">We Never Sell Data:</strong> We do not sell, rent, monetize, or broker any customer information to third parties or brokers under any circumstances.</li>
                <li><strong className="text-text-main">No Ad Targeting:</strong> Conversation data, phone numbers, and customer queries are never used for commercial ad targeting, behavioral profiling, or advertising networks.</li>
                <li><strong className="text-text-main">No Cross-Tenant Training:</strong> Tenant A's customer data and Knowledge Base are never used to train models for or shared with Tenant B. Data is strictly isolated per tenant.</li>
              </ul>
            </section>

            {/* 5. Storage & Encryption */}
            <section id="encryption" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Lock className="text-brand-primary" size={22} />
                <h2>5. Storage & Encryption Standards</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                We employ enterprise-grade security protocols to protect all stored information:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 border border-brand-border rounded-xl bg-white space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-brand-dark">
                    <Server size={16} className="text-brand-primary" />
                    Encryption at Rest
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    All tenant databases, access tokens, and message logs are hosted on <strong>Neon PostgreSQL</strong> clusters protected with full AES-256 block-level encryption at rest.
                  </p>
                </div>
                <div className="p-4 border border-brand-border rounded-xl bg-white space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-brand-dark">
                    <Lock size={16} className="text-brand-primary" />
                    Encryption in Transit
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    All network traffic between users, webhooks, and backend APIs is secured with strict <strong>TLS 1.3 / HTTPS</strong> transport encryption.
                  </p>
                </div>
              </div>
            </section>

            {/* 6. Data Retention & Deletion */}
            <section id="retention" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Database className="text-brand-primary" size={22} />
                <h2>6. Data Retention & Deletion</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                Data is retained only as long as required to serve customer conversations or until the Business Tenant or end-customer requests deletion.
              </p>
              <p className="text-text-muted text-sm leading-relaxed">
                To request immediate data deletion, visit our dedicated <Link to="/data-deletion" className="text-brand-primary font-semibold hover:underline">Data Deletion Portal</Link> or email <a href="mailto:privacy@ravisn.com" className="text-brand-primary hover:underline">privacy@ravisn.com</a>.
              </p>
            </section>

            {/* 7. Your Rights */}
            <section id="user-rights" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <HelpCircle className="text-brand-primary" size={22} />
                <h2>7. Your Rights & Regulatory Compliance</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                Under global privacy frameworks (including GDPR, CCPA, and Meta Platform Policies), users have the right to:
              </p>
              <ul className="space-y-1.5 text-xs text-text-muted list-disc list-inside">
                <li>Request access to all stored conversation logs associated with their identifier.</li>
                <li>Request correction of inaccurate booking or contact details.</li>
                <li>Request complete erasure (the "Right to be Forgotten") of all personal data.</li>
                <li>Revoke platform authorization directly through Facebook/Instagram settings.</li>
              </ul>
            </section>

            {/* 8. Contact Information */}
            <section id="contact" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Mail className="text-brand-primary" size={22} />
                <h2>8. Contact Information</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                For questions regarding this policy or data privacy inquiries:
              </p>
              <div className="p-4 border border-brand-border rounded-xl bg-brand-bg text-xs space-y-1 text-text-muted">
                <p><strong>RAVISN Privacy & Compliance Office</strong></p>
                <p>Lahore, Punjab, Pakistan</p>
                <p>Official Website: <a href="https://tryravisn.com" target="_blank" rel="noopener noreferrer" className="text-brand-primary hover:underline font-medium">https://tryravisn.com</a></p>
                <p>Privacy Email: <a href="mailto:privacy@ravisn.com" className="text-brand-primary hover:underline font-medium">privacy@ravisn.com</a></p>
                <p>Support Email: <a href="mailto:support@ravisn.com" className="text-brand-primary hover:underline font-medium">support@ravisn.com</a></p>
              </div>
            </section>
          </div>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
