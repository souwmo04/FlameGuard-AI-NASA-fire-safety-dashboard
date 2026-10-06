"use client";

import { useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";

interface Star {
  x: number;
  y: number;
  z: number; // depth 0.2 (far) .. 1 (near): size, brightness and drift speed
  phase: number;
}

/**
 * Subtle animated star field (canvas). Pauses while the tab is hidden and renders a single static
 * frame when the user prefers reduced motion.
 */
export function Starfield({ density = 0.00012, className }: { density?: number; className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    let stars: Star[] = [];
    let width = 0;
    let height = 0;
    let frame = 0;
    let running = true;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.max(80, Math.floor(width * height * density));
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        z: 0.2 + Math.random() * 0.8,
        phase: Math.random() * Math.PI * 2,
      }));
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, width, height);
      for (const s of stars) {
        const twinkle = reduce ? 1 : 0.65 + 0.35 * Math.sin(t / 900 + s.phase);
        const r = s.z * 1.3;
        ctx.globalAlpha = Math.min(1, 0.25 + s.z * 0.75) * twinkle;
        ctx.fillStyle = s.z > 0.85 ? "#fde68a" : s.z > 0.6 ? "#e0f2fe" : "#94a3b8";
        ctx.beginPath();
        ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
        ctx.fill();
        if (!reduce) {
          s.x -= s.z * 0.05; // slow parallax drift
          if (s.x < -2) s.x = width + 2;
        }
      }
      ctx.globalAlpha = 1;
    };

    const loop = (t: number) => {
      if (!running) return;
      draw(t);
      frame = requestAnimationFrame(loop);
    };

    const onVisibility = () => {
      running = !document.hidden && !reduce;
      cancelAnimationFrame(frame);
      if (running) frame = requestAnimationFrame(loop);
    };

    resize();
    if (reduce) {
      draw(0);
    } else {
      frame = requestAnimationFrame(loop);
    }
    window.addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      running = false;
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [density, reduce]);

  return <canvas ref={canvasRef} aria-hidden="true" className={className} />;
}
