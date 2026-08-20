import { Link2, MessageCircle, Calendar, BookOpen, Sliders, Settings as SettingsIcon, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import RavisnLogo from "./RavisnLogo";

const NAV_ITEMS = [
  { key: "connect", label: "Connect", icon: Link2 },
  { key: "inbox", label: "Inbox", icon: MessageCircle },
  { key: "bookings", label: "Bookings", icon: Calendar },
  { key: "knowledge", label: "Knowledge base", icon: BookOpen },
  { key: "system-prompt", label: "System Prompt Tuning", icon: Sliders },
  { key: "settings", label: "Settings", icon: SettingsIcon },
];

export default function Sidebar({ active, onSelect }) {
  const { user, logout } = useAuth();

  return (
    <div className="w-60 flex-shrink-0 bg-brand-dark text-white flex flex-col h-screen sticky top-0 border-r border-brand-border-dark">
      <div className="px-5 py-4 border-b border-brand-border-dark flex items-center justify-between">
        <RavisnLogo variant="light" size="sm" />
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => onSelect(key)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
              active === key
                ? "bg-brand-primary text-white font-semibold shadow-xs"
                : "text-white/70 hover:text-white hover:bg-white/10"
            }`}
          >
            <Icon size={18} strokeWidth={1.75} />
            {label}
          </button>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-brand-border-dark">
        <div className="px-3 pb-2 text-xs text-white/50 truncate font-medium">{user?.tenant?.name}</div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/10 transition"
        >
          <LogOut size={18} strokeWidth={1.75} />
          Log out
        </button>
      </div>
    </div>
  );
}
