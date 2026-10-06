import Link from "next/link";
import type { ComponentProps } from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-gradient-to-r from-flame to-ember text-space-950 shadow-[0_0_32px_-6px_rgb(251_146_60/0.6)] hover:shadow-[0_0_44px_-4px_rgb(251_146_60/0.75)]",
  secondary: "glass text-ink hover:border-plasma/40 hover:text-plasma",
};

/** Call-to-action link styled as a button. */
export function ButtonLink({ variant = "primary", className, ...props }: ComponentProps<typeof Link> & { variant?: Variant }) {
  return (
    <Link
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition duration-200",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}
