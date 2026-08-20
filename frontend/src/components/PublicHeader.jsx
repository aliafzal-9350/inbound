import { Link, useLocation } from "react-router-dom";
import { ShieldCheck, FileText, Trash2, ArrowRight, ExternalLink } from "lucide-react";
import RavisnLogo from "./RavisnLogo";

export default function PublicHeader() {
  const location = useLocation();

  const navLinks = [
    { name: "Privacy Policy", path: "/privacy", icon: ShieldCheck },
    { name: "Terms of Service", path: "/terms", icon: FileText },
    { name: "Data Deletion", path: "/data-deletion", icon: Trash2 },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-brand-border shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Home Link */}
          <div className="flex items-center gap-6">
            <a
              href="https://tryravisn.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 group focus:outline-none"
            >
              <RavisnLogo variant="dark" size="sm" />
            </a>

            <div className="hidden sm:flex items-center gap-1.5 pl-3 border-l border-brand-border">
              <a
                href="https://tryravisn.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-text-muted hover:text-brand-primary flex items-center gap-1 font-medium px-2 py-1 rounded-md hover:bg-brand-primary-light transition-colors"
              >
                tryravisn.com
                <ExternalLink size={12} className="opacity-60" />
              </a>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-brand-primary-light text-brand-primary font-semibold shadow-2xs"
                      : "text-text-muted hover:text-brand-dark hover:bg-gray-100/80"
                  }`}
                >
                  <Icon size={14} className={isActive ? "text-brand-primary" : "text-text-muted"} />
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-2.5">
            <Link
              to="/login"
              className="text-xs font-semibold text-text-main hover:text-brand-primary px-3.5 py-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-primary hover:bg-brand-primary-hover text-white text-xs font-semibold shadow-xs hover:shadow-sm transition-all duration-150"
            >
              <span>Workspace</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
