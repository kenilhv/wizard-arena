import type { SVGProps } from "react";

/* Minimal stroke icons (Lucide-style). Inherit color via currentColor. */

type P = SVGProps<SVGSVGElement> & { size?: number };

function Svg({ size = 18, children, ...rest }: P & { children: React.ReactNode }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
      {...rest}
    >
      {children}
    </svg>
  );
}

// Head-to-head (two crossed swords)
export const IconSwords = (p: P) => (
  <Svg {...p}>
    <path d="M14.5 17.5 4 7V4h3l10.5 10.5" />
    <path d="m13 19 6-6" /><path d="m16 16 4 4" /><path d="m19 21 2-2" />
    <path d="M9.5 17.5 20 7V4h-3L6.5 14.5" />
    <path d="m11 19-6-6" /><path d="m8 16-4 4" /><path d="m5 21-2-2" />
  </Svg>
);

// Research (magnifier)
export const IconSearch = (p: P) => (
  <Svg {...p}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></Svg>
);

// Coding / task (terminal)
export const IconTerminal = (p: P) => (
  <Svg {...p}><path d="m4 17 6-5-6-5" /><path d="M12 19h8" /></Svg>
);

// Trophy (leaderboard)
export const IconTrophy = (p: P) => (
  <Svg {...p}>
    <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
    <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
    <path d="M4 22h16" /><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
    <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
    <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
  </Svg>
);

// Submit (upload)
export const IconUpload = (p: P) => (
  <Svg {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 9 5-5 5 5" /><path d="M12 4v12" /></Svg>
);

// Run / play
export const IconBolt = (p: P) => (
  <Svg {...p}><path d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z" /></Svg>
);

// Admin / shield
export const IconShield = (p: P) => (
  <Svg {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /></Svg>
);

// Host / gauge
export const IconGauge = (p: P) => (
  <Svg {...p}><path d="m12 14 4-4" /><path d="M3.34 19a10 10 0 1 1 17.32 0" /></Svg>
);

export const IconArrowLeft = (p: P) => (
  <Svg {...p}><path d="m12 19-7-7 7-7" /><path d="M19 12H5" /></Svg>
);

// User
export const IconUser = (p: P) => (
  <Svg {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></Svg>
);

// Live dot (filled)
export const Dot = ({ color = "currentColor", size = 8 }: { color?: string; size?: number }) => (
  <span style={{
    width: size, height: size, borderRadius: 999, background: color,
    display: "inline-block", boxShadow: `0 0 8px ${color}`,
  }} />
);

export function problemIcon(slug: string, kind: string, size = 22) {
  if (kind === "h2h") return <IconSwords size={size} />;
  if (slug === "research-agent") return <IconSearch size={size} />;
  return <IconTerminal size={size} />;
}
