"use client";

import { useMotionValueEvent, useReducedMotion, useSpring } from "motion/react";
import { useEffect, useState } from "react";

interface AnimatedNumberProps {
  value: number;
  format?: (n: number) => string;
  className?: string;
}

/** Rolls smoothly to a new value; jumps straight there when the user prefers reduced motion. */
export function AnimatedNumber({ value, format = (n) => Math.round(n).toString(), className }: AnimatedNumberProps) {
  const reduce = useReducedMotion();
  const spring = useSpring(0, { stiffness: 90, damping: 22, mass: 0.8 });
  const [display, setDisplay] = useState(() => format(0));

  useMotionValueEvent(spring, "change", (latest) => setDisplay(format(latest)));

  useEffect(() => {
    // No animation frames run in a background tab, so a count-up would sit at 0 until the user
    // returns: jump straight to the value instead (also for users who prefer reduced motion).
    if (reduce || document.visibilityState === "hidden") spring.jump(value);
    else spring.set(value);
  }, [value, reduce, spring]);

  // With reduced motion the final value is shown directly; otherwise the spring's current value.
  const shown = reduce ? format(value) : display;
  return (
    <span className={className} aria-label={format(value)}>
      <span aria-hidden="true">{shown}</span>
    </span>
  );
}
