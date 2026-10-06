import {
  BookOpen,
  BrainCircuit,
  Earth,
  FlaskConical,
  Flame,
  GitCompareArrows,
  LayoutDashboard,
  type LucideIcon,
  Radar,
  SlidersHorizontal,
  Trophy,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  description: string;
  group: "Mission" | "Analysis" | "Knowledge";
  /** shown in the mobile bottom bar */
  primary?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Mission Control", icon: LayoutDashboard, group: "Mission", primary: true,
    description: "Live overview of the data, the model and its evidence" },
  { href: "/risk", label: "Fire Risk", icon: Flame, group: "Mission", primary: true,
    description: "Analyze the fire risk of a combustion scenario" },
  { href: "/what-if", label: "What-If Lab", icon: SlidersHorizontal, group: "Mission", primary: true,
    description: "Compare two scenarios step by step" },
  { href: "/experiments", label: "Experiments", icon: FlaskConical, group: "Analysis", primary: true,
    description: "Explore all 274 NASA FLEX tests" },
  { href: "/ranking", label: "Ranking", icon: Trophy, group: "Analysis",
    description: "Rank tests and tested conditions" },
  { href: "/suppressants", label: "Suppressant Lab", icon: GitCompareArrows, group: "Analysis",
    description: "N₂ vs CO₂ vs He — what the observed data supports" },
  { href: "/similar", label: "Similar Tests", icon: Radar, group: "Analysis",
    description: "Find the NASA tests closest to your conditions" },
  { href: "/knowledge", label: "Ask FlameGuard", icon: BrainCircuit, group: "Knowledge",
    description: "Questions answered from NASA documents, with citations" },
  { href: "/science", label: "Microgravity Science", icon: Earth, group: "Knowledge",
    description: "Why flames behave differently in space" },
  { href: "/methodology", label: "Methodology", icon: BookOpen, group: "Knowledge",
    description: "Data, model, validation and limitations" },
];

export const NAV_GROUPS = ["Mission", "Analysis", "Knowledge"] as const;
