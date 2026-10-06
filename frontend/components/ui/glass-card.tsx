import type { ComponentPropsWithoutRef, ElementType } from "react";

import { cn } from "@/lib/cn";

type GlassCardProps<T extends ElementType> = {
  as?: T;
  /** subtle flame-coloured edge glow for featured panels */
  glow?: boolean;
} & ComponentPropsWithoutRef<T>;

/** Translucent panel with a hairline border — the base surface of the interface. */
export function GlassCard<T extends ElementType = "div">({ as, glow, className, ...props }: GlassCardProps<T>) {
  const Tag = (as ?? "div") as ElementType;
  return (
    <Tag
      className={cn(
        "glass relative rounded-2xl",
        glow &&
          "before:pointer-events-none before:absolute before:inset-0 before:rounded-2xl before:bg-[radial-gradient(120%_80%_at_0%_0%,rgb(251_191_36/0.10),transparent_60%)]",
        className,
      )}
      {...props}
    />
  );
}
