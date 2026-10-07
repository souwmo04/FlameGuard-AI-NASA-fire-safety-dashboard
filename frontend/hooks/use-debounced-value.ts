"use client";

import { useEffect, useState } from "react";

/** The value, updated only after it has stopped changing for `delay` ms (e.g. while a slider is dragged). */
export function useDebouncedValue<T>(value: T, delay = 220): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}
