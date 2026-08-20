import { Link } from "react-router-dom";
import { ShieldCheck, FileText, Trash2, Mail, Globe, MapPin } from "lucide-react";
import RavisnLogo from "./RavisnLogo";

export default function PublicFooter() {
  return (
    <footer className="bg-brand-dark text-white border-t border-brand-border-dark mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Col */}
          <div className="space-y-4 md:col-span-2">
            <RavisnLogo variant="light" size="md" />
            <p className="text-text-muted text-xs leading-relaxed max-w-sm">
              Enterprise conversational AI agent platform connecting WhatsApp Cloud API, Meta Messenger, and Instagram Direct with strict zero-hallucination knowledge grounding.
            </p>
            <div className="flex items-center gap-4 text-xs text-text-muted pt-1">
              <span className="flex items-center gap-1.5">
                <MapPin size={13} className="text-brand-primary" />
                Lahore, Pakistan
              </span>
              <a
                href="https://tryravisn.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:text-brand-primary transition-colors"
              >
                <Globe size={13} className="text-brand-primary" />
                tryravisn.com
              </a>
            </div>
          </div>

          {/* Compliance & Legal */}
          <div>
            <h4 className="font-semibold text-xs text-white uppercase tracking-wider mb-3">
              Compliance & Legal
            </h4>
            <ul className="space-y-2 text-xs text-text-muted">
              <li>
                <Link to="/privacy" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <ShieldCheck size={13} className="text-brand-primary" />
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <FileText size={13} className="text-brand-primary" />
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link to="/data-deletion" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <Trash2 size={13} className="text-brand-primary" />
                  Data Deletion Instructions
                </Link>
              </li>
            </ul>
          </div>

          {/* Support & Contact */}
          <div>
            <h4 className="font-semibold text-xs text-white uppercase tracking-wider mb-3">
              Contact & Support
            </h4>
            <ul className="space-y-2 text-xs text-text-muted">
              <li>
                <a href="mailto:support@ravisn.com" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <Mail size={13} className="text-brand-primary" />
                  support@ravisn.com
                </a>
              </li>
              <li>
                <a href="mailto:privacy@ravisn.com" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <Mail size={13} className="text-brand-primary" />
                  privacy@ravisn.com
                </a>
              </li>
              <li>
                <a href="mailto:legal@ravisn.com" className="hover:text-white flex items-center gap-1.5 transition-colors">
                  <Mail size={13} className="text-brand-primary" />
                  legal@ravisn.com
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-brand-border-dark mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-text-muted">
          <p>© 2026 RAVISN. All rights reserved.</p>
          <p className="mt-2 sm:mt-0 text-[11px]">
            Meta, WhatsApp, Facebook, and Instagram are registered trademarks of Meta Platforms, Inc.
          </p>
        </div>
      </div>
    </footer>
  );
}
