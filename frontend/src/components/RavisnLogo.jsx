export default function RavisnLogo({
  variant = "dark", // "dark" | "light"
  showText = true,
  size = "md", // "sm" | "md" | "lg" | "xl"
  useOriginal = false, // if true, uses /original one.jpeg
  className = "",
}) {
  const sizeMap = {
    sm: { img: "h-7 w-auto", text: "text-base tracking-wider", subtext: "text-[8px]" },
    md: { img: "h-9 w-auto", text: "text-xl tracking-widest", subtext: "text-[9px]" },
    lg: { img: "h-12 w-auto", text: "text-2xl tracking-widest", subtext: "text-[10px]" },
    xl: { img: "h-16 w-auto", text: "text-4xl tracking-widest", subtext: "text-xs" },
  };

  const currentSize = sizeMap[size] || sizeMap.md;
  const isLight = variant === "light";
  const textColor = isLight ? "text-white" : "text-brand-dark";
  const subtextColor = isLight ? "text-white/60" : "text-text-muted";

  if (useOriginal) {
    return (
      <div className={`inline-flex items-center select-none ${className}`}>
        <img
          src="/original one.jpeg"
          alt="RAVISN"
          className={`${currentSize.img} object-contain transition-transform duration-200`}
        />
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      {/* Official favicon.png logo image without circular wrapper */}
      <img
        src="/favicon.png"
        alt="RAVISN"
        className={`${currentSize.img} object-contain flex-shrink-0 transition-transform duration-200`}
      />

      {/* High-contrast brand typography */}
      {showText && (
        <div className="flex flex-col leading-none">
          <span className={`font-display font-extrabold ${currentSize.text} ${textColor} transition-colors`}>
            RAVISN
          </span>
          <span className={`font-mono uppercase font-semibold tracking-widest ${currentSize.subtext} ${subtextColor} mt-0.5`}>
            AI AGENT
          </span>
        </div>
      )}
    </div>
  );
}
