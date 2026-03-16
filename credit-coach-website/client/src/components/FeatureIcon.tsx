import type { ReactNode } from "react";

export type FeatureIconName =
  | "decision"
  | "roadmap"
  | "offer"
  | "governance"
  | "learning"
  | "portfolio"
  | "platform"
  | "proof"
  | "market"
  | "contact"
  | "demo"
  | "process";

type FeatureIconProps = {
  name: FeatureIconName;
  className?: string;
};

export function FeatureIcon({ name, className = "h-6 w-6" }: FeatureIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {iconPaths[name]}
    </svg>
  );
}

const iconPaths: Record<FeatureIconName, ReactNode> = {
  decision: (
    <>
      <path d="M4 6h16" />
      <path d="M4 12h10" />
      <path d="M4 18h7" />
      <path d="M17 10l3 2-3 2" />
    </>
  ),
  roadmap: (
    <>
      <circle cx="6" cy="18" r="2.2" />
      <circle cx="12" cy="10" r="2.2" />
      <circle cx="18" cy="6" r="2.2" />
      <path d="M7.8 16.5 10.2 11.5" />
      <path d="M13.8 8.7 16.2 7.3" />
      <path d="M18 6v8" />
      <path d="M18 14l2.5-2.5" />
    </>
  ),
  offer: (
    <>
      <path d="M4 7h16v10H4z" />
      <path d="M8 11h8" />
      <path d="M8 15h5" />
      <circle cx="17" cy="15" r="1.8" />
    </>
  ),
  governance: (
    <>
      <path d="M12 3 6 5.5V11c0 4 2.6 7 6 8 3.4-1 6-4 6-8V5.5L12 3Z" />
      <path d="m9.5 11.5 1.7 1.7 3.8-4.2" />
    </>
  ),
  learning: (
    <>
      <path d="M7 7h7a4 4 0 1 1 0 8H8" />
      <path d="m7 7 2-2" />
      <path d="m7 7 2 2" />
      <path d="M17 17l-2 2" />
      <path d="m17 17-2-2" />
    </>
  ),
  portfolio: (
    <>
      <path d="M5 19V9" />
      <path d="M12 19V5" />
      <path d="M19 19v-7" />
      <path d="M3 19h18" />
    </>
  ),
  platform: (
    <>
      <path d="M12 4 5 8l7 4 7-4-7-4Z" />
      <path d="m5 12 7 4 7-4" />
      <path d="m5 16 7 4 7-4" />
    </>
  ),
  proof: (
    <>
      <path d="M7 4h8l4 4v12H7z" />
      <path d="M15 4v4h4" />
      <path d="m10 14 2 2 4-5" />
    </>
  ),
  market: (
    <>
      <path d="M4 18h16" />
      <path d="M6 15.5 10 11l3 2.5L19 6" />
      <path d="m16 6 3 0v3" />
    </>
  ),
  contact: (
    <>
      <path d="M4 7h16v10H4z" />
      <path d="m4 8 8 5 8-5" />
    </>
  ),
  demo: (
    <>
      <rect x="4" y="5" width="16" height="11" rx="2" />
      <path d="M8 20h8" />
      <path d="M12 16v4" />
      <path d="m10 9 4 2.5-4 2.5z" />
    </>
  ),
  process: (
    <>
      <circle cx="6" cy="12" r="2" />
      <circle cx="12" cy="6" r="2" />
      <circle cx="18" cy="12" r="2" />
      <circle cx="12" cy="18" r="2" />
      <path d="M7.6 10.7 10.4 7.3" />
      <path d="M13.6 7.3 16.4 10.7" />
      <path d="M16.4 13.3 13.6 16.7" />
      <path d="M10.4 16.7 7.6 13.3" />
    </>
  ),
};
