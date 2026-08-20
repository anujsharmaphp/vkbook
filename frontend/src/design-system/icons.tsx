import type { FC, SVGProps } from "react";

function Icon({ children, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export function CricketIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <line x1="10" y1="2.5" x2="10" y2="9" />
      <ellipse cx="10" cy="14" rx="3.6" ry="5.5" />
    </Icon>
  );
}

export function FootballIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.3} {...props}>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M10 6.3l2.3 1.7-.9 2.7H8.6l-.9-2.7z" />
      <path d="M10 6.3V3.3M12.3 8l2.7-1M11.4 10.7l1.7 2.4M8.6 10.7l-1.7 2.4M7.7 8l-2.7-1" />
    </Icon>
  );
}

export function TennisIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M3.6 5.8c3 1.4 3 7 0 8.4" />
      <path d="M16.4 5.8c-3 1.4-3 7 0 8.4" />
    </Icon>
  );
}

export function RugbyIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M3.4 10c0-3.2 2.6-5.6 6.6-5.6s6.6 2.4 6.6 5.6-2.6 5.6-6.6 5.6-6.6-2.4-6.6-5.6z" />
      <path d="M5.6 10h8.8M8.2 8.6v2.8M11.8 8.6v2.8" />
    </Icon>
  );
}

export function BasketballIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.3} {...props}>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M10 2.5v15M2.5 10h15" />
      <path d="M4.6 4.8c2.8 1.9 2.8 8.5 0 10.4M15.4 4.8c-2.8 1.9-2.8 8.5 0 10.4" />
    </Icon>
  );
}

export function GolfIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M6.2 3v13.4" />
      <path d="M6.2 3.8l6 2.5-6 2.5z" />
      <ellipse cx="6.2" cy="16.6" rx="4.6" ry="1.3" />
    </Icon>
  );
}

export function HorseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M5.3 8.6a4.7 4.7 0 019.4 0v3.6a1.3 1.3 0 01-2.6 0V8.6a2 2 0 00-4.2 0v3.6a1.3 1.3 0 01-2.6 0z" />
    </Icon>
  );
}

export function CasinoIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="4" y="4" width="12" height="12" rx="2" />
      <circle cx="7.3" cy="7.3" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="10" cy="10" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="12.7" cy="12.7" r="0.9" fill="currentColor" stroke="none" />
    </Icon>
  );
}

export function GenericSportIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx="10" cy="10" r="7.5" />
    </Icon>
  );
}

const SPORT_ICONS: Record<string, FC<SVGProps<SVGSVGElement>>> = {
  CRICKET: CricketIcon,
  FOOTBALL: FootballIcon,
  SOCCER: FootballIcon,
  TENNIS: TennisIcon,
  RUGBY: RugbyIcon,
  BASKETBALL: BasketballIcon,
  GOLF: GolfIcon,
  HORSE_RACING: HorseIcon,
  CASINO: CasinoIcon,
};

export function sportIconFor(code: string) {
  return SPORT_ICONS[code.toUpperCase()] ?? GenericSportIcon;
}

export function ChevronDownIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.6} {...props}>
      <path d="M5 8l5 5 5-5" />
    </Icon>
  );
}

export function SearchIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.6} {...props}>
      <circle cx="9" cy="9" r="6" />
      <path d="M17 17l-4-4" />
    </Icon>
  );
}

export function BellIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.5} {...props}>
      <path d="M6 8a4 4 0 018 0c0 4 1.6 5 1.6 5H4.4S6 12 6 8z" />
      <path d="M8.4 15.5a1.7 1.7 0 003.2 0" />
    </Icon>
  );
}

export function SunMoonIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.5} {...props}>
      <circle cx="10" cy="10" r="3.6" />
      <path d="M10 2.6v2M10 15.4v2M17.4 10h-2M4.6 10h-2M15.2 4.8l-1.4 1.4M6.2 13.8l-1.4 1.4M15.2 15.2l-1.4-1.4M6.2 6.2L4.8 4.8" />
    </Icon>
  );
}

export function CloseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.6} {...props}>
      <path d="M5 5l10 10M15 5L5 15" />
    </Icon>
  );
}

export function EmptySlipIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.3} {...props}>
      <rect x="4" y="3" width="12" height="14" rx="2" />
      <path d="M7 7.5h6M7 10.5h6M7 13.5h3.5" />
    </Icon>
  );
}

export function InfoIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M10 9.2v5M10 6.3v.02" />
    </Icon>
  );
}

export function LogoutIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon strokeWidth={1.5} {...props}>
      <path d="M8 3H4.5A1.5 1.5 0 003 4.5v11A1.5 1.5 0 004.5 17H8" />
      <path d="M12.5 13.5L17 9l-4.5-4.5M17 9H7.5" />
    </Icon>
  );
}
