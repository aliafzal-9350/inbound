import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import { FileText, CheckCircle2, AlertTriangle, ShieldCheck, Scale, RefreshCw, Mail } from "lucide-react";

export default function TermsConditions() {
  const [activeSection, setActiveSection] = useState("acceptance");

  const sections = [
    { id: "acceptance", label: "1. Acceptance of Terms" },
    { id: "service-scope", label: "2. Service Scope & Availability" },
    { id: "acceptable-use", label: "3. Acceptable Use Policy" },
    { id: "meta-compliance", label: "4. Meta Platform Terms Compliance" },
    { id: "quotas", label: "5. API Quotas & Fair Usage" },
    { id: "suspension", label: "6. Suspension & Termination" },
    { id: "liability", label: "7. Limitation of Liability" },
    { id: "governing-law", label: "8. Governing Law & Contact" },
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
            <Scale size={14} />
            Enterprise Service Agreement
          </div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-brand-dark mb-2">
            Terms of Service & SaaS Agreement
          </h1>
          <p className="text-text-muted text-sm sm:text-base max-w-3xl">
            These terms govern your access to and use of the RAVISN conversational AI platform, API endpoints, dashboard workspaces, and integrated Meta messaging channels.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-6 pt-6 border-t border-brand-border text-xs text-text-muted">
            <span><strong>Effective Date:</strong> January 1, 2026</span>
            <span>•</span>
            <span><strong>Last Updated:</strong> August 20, 2026</span>
            <span>•</span>
            <span><strong>Version:</strong> 2.4 Enterprise</span>
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
                  to="/privacy"
                  className="flex items-center justify-between text-xs font-semibold text-brand-primary hover:underline"
                >
                  <span>Read Privacy Policy</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          </aside>

          {/* Main Legal Document Content */}
          <div className="lg:col-span-8 bg-white border border-brand-border rounded-2xl p-6 sm:p-10 shadow-xs space-y-10">
            {/* 1. Acceptance */}
            <section id="acceptance" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <FileText className="text-brand-primary" size={22} />
                <h2>1. Acceptance of Terms</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                By creating an account, connecting a Meta asset (WhatsApp Phone Number, Facebook Page, or Instagram Professional Account), or utilizing the RAVISN conversational API, you ("Tenant", "Customer", or "User") agree to be bound by these Terms of Service. If you are entering into this agreement on behalf of a company or legal entity, you represent that you have the authority to bind such entity.
              </p>
            </section>

            {/* 2. Service Scope & Availability */}
            <section id="service-scope" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <RefreshCw className="text-brand-primary" size={22} />
                <h2>2. Service Scope & Service Level Commitment (SLA)</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                RAVISN provides an AI-powered conversational platform that ingests inbound messages, queries the Tenant's Knowledge Base, generates responses, and extracts appointment leads.
              </p>
              <div className="p-4 border border-brand-border rounded-xl bg-brand-bg text-xs space-y-2 text-text-muted">
                <div className="flex items-center gap-2 font-bold text-text-main">
                  <CheckCircle2 size={16} className="text-emerald-600" />
                  Service Level Commitment
                </div>
                <p>
                  RAVISN targets a <strong>99.9% monthly service uptime</strong> for our core API endpoints and webhook ingestion gateways, excluding scheduled maintenance windows and third-party platform outages (e.g., Meta Graph API status disruptions).
                </p>
              </div>
            </section>

            {/* 3. Acceptable Use Policy */}
            <section id="acceptable-use" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <AlertTriangle className="text-brand-primary" size={22} />
                <h2>3. Acceptable Use Policy (AUP)</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                You agree not to use the RAVISN platform for any unlawful, harassing, fraudulent, or harmful activities, including but not limited to:
              </p>
              <ul className="space-y-1.5 text-xs text-text-muted list-disc list-inside">
                <li>Transmitting unsolicited promotional spam, bulk marketing blasts in violation of WhatsApp Business policies, or deceptive messages.</li>
                <li>Impersonating medical professionals, financial regulators, or government entities without verified credentials.</li>
                <li>Attempting to reverse-engineer the RAVISN backend engine, bypass tenant isolation security boundaries, or execute unauthorized vulnerability testing.</li>
                <li>Uploading knowledge base documents containing copyrighted materials without authorization or illegal content.</li>
              </ul>
            </section>

            {/* 4. Meta Platform Compliance */}
            <section id="meta-compliance" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <ShieldCheck className="text-brand-primary" size={22} />
                <h2>4. Meta Platform Terms Compliance</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                When connecting WhatsApp, Facebook, or Instagram channels to RAVISN, you explicitly agree to comply with:
              </p>
              <ul className="space-y-1 text-xs text-text-muted list-disc list-inside">
                <li><strong>WhatsApp Business Messaging Policy</strong> and 24-hour customer care messaging window rules.</li>
                <li><strong>Meta Platform Terms</strong> and Developer Policies.</li>
                <li><strong>Instagram Community Guidelines</strong> and Commercial Messaging Guidelines.</li>
              </ul>
              <p className="text-text-muted text-xs leading-relaxed pt-1">
                Violation of Meta policies may result in immediate suspension of the associated channel by Meta Platforms, Inc., for which RAVISN bears no liability.
              </p>
            </section>

            {/* 5. API Quotas & Fair Usage */}
            <section id="quotas" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Scale className="text-brand-primary" size={22} />
                <h2>5. API Quotas & Fair Usage</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                To preserve system stability and sub-second latency across all tenants, accounts are subject to fair usage limits based on their active plan:
              </p>
              <ul className="space-y-1 text-xs text-text-muted list-disc list-inside">
                <li>Automated rate-limiting applies to concurrent webhook processing and knowledge base document uploads.</li>
                <li>Excessive bursts exceeding contracted throughput will be queued gracefully to prevent message dropping.</li>
              </ul>
            </section>

            {/* 6. Suspension & Termination */}
            <section id="suspension" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <AlertTriangle className="text-brand-primary" size={22} />
                <h2>6. Suspension & Termination</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                We reserve the right to suspend or terminate tenant access immediately upon notice if:
              </p>
              <ul className="space-y-1 text-xs text-text-muted list-disc list-inside">
                <li>The Tenant breaches these Terms of Service or Meta Platform Guidelines.</li>
                <li>Required subscription fees are overdue beyond the grace period.</li>
                <li>The Tenant’s usage presents a security vulnerability or operational risk to other tenants.</li>
              </ul>
            </section>

            {/* 7. Limitation of Liability */}
            <section id="liability" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Scale className="text-brand-primary" size={22} />
                <h2>7. Limitation of Liability & Warranty Disclaimer</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, RAVISN PROVIDES THE SERVICES "AS IS" AND "AS AVAILABLE." RAVISN DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS, IMPLIED, OR STATUTORY. IN NO EVENT SHALL RAVISN BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES (INCLUDING LOSS OF PROFITS OR DATA) ARISING OUT OF YOUR USE OF THE SERVICES.
              </p>
            </section>

            {/* 8. Governing Law */}
            <section id="governing-law" className="scroll-mt-28 space-y-4">
              <div className="flex items-center gap-2.5 text-brand-dark font-display text-xl font-bold border-b border-brand-border pb-3">
                <Mail className="text-brand-primary" size={22} />
                <h2>8. Governing Law & Inquiries</h2>
              </div>
              <p className="text-text-muted text-sm leading-relaxed">
                These terms are governed by the laws of Pakistan. For enterprise agreements or legal inquiries:
              </p>
              <div className="p-4 border border-brand-border rounded-xl bg-brand-bg text-xs space-y-1 text-text-muted">
                <p><strong>RAVISN Legal Department</strong></p>
                <p>Lahore, Punjab, Pakistan</p>
                <p>Email: <a href="mailto:legal@ravisn.com" className="text-brand-primary hover:underline font-medium">legal@ravisn.com</a></p>
                <p>Support: <a href="mailto:support@ravisn.com" className="text-brand-primary hover:underline font-medium">support@ravisn.com</a></p>
              </div>
            </section>
          </div>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
