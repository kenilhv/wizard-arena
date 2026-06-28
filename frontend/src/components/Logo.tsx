/* Arena brand mark — a champion's podium under a guiding star.
   Reads as competition / leaderboard; deep indigo→violet→gold (no neon). */

export function LogoMark({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 56 56" fill="none" aria-hidden>
      <defs>
        <linearGradient id="arena-tile" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#241a52" />
          <stop offset="1" stopColor="#12102e" />
        </linearGradient>
        <linearGradient id="arena-edge" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#a78bfa" />
          <stop offset="0.5" stopColor="#6366f1" />
          <stop offset="1" stopColor="#22d3ee" />
        </linearGradient>
        <linearGradient id="arena-gold" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fcd34d" />
          <stop offset="1" stopColor="#d99e2b" />
        </linearGradient>
        <linearGradient id="arena-bar" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#c4b5fd" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>

      {/* tile */}
      <rect x="2.5" y="2.5" width="51" height="51" rx="15"
        fill="url(#arena-tile)" stroke="url(#arena-edge)" strokeWidth="2" />

      {/* podium: left (3rd) · center (1st) · right (2nd) */}
      <rect x="11" y="33" width="10" height="13" rx="2.5" fill="url(#arena-bar)" opacity="0.75" />
      <rect x="35" y="29" width="10" height="17" rx="2.5" fill="url(#arena-bar)" opacity="0.9" />
      <rect x="23" y="22" width="10" height="24" rx="2.5" fill="url(#arena-gold)" />

      {/* guiding star above the winner */}
      <path
        d="M28 8.5 L29.7 13.1 L34.5 13.4 L30.8 16.5 L32 21.2 L28 18.5 L24 21.2 L25.2 16.5 L21.5 13.4 L26.3 13.1 Z"
        fill="url(#arena-gold)"
      />
    </svg>
  );
}

export default function Logo({ size = 40, showWord = true }: { size?: number; showWord?: boolean }) {
  return (
    <span className="inline-flex items-center gap-3 select-none">
      <LogoMark size={size} />
      {showWord && (
        <span className="flex flex-col leading-none">
          <span className="wordmark text-2xl md:text-3xl font-black tracking-[0.18em]">ARENA</span>
          <span className="text-[10px] md:text-[11px] tracking-[0.22em] uppercase text-[var(--color-muted)] mt-1">
            Harness League
          </span>
        </span>
      )}
    </span>
  );
}
