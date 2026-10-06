/**
 * Hero visual: a near-spherical flame around a fuel droplet, as in microgravity, inside slowly
 * rotating orbital lines. Decorative (aria-hidden); the caption beside it carries the meaning.
 */
export function FlameOrb({ className }: { className?: string }) {
  return (
    <div aria-hidden="true" className={className}>
      <div className="relative aspect-square w-full">
        {/* orbits */}
        <svg viewBox="0 0 400 400" className="absolute inset-0 size-full animate-orbit">
          <ellipse cx="200" cy="200" rx="190" ry="78" fill="none" stroke="#22d3ee" strokeOpacity="0.22" strokeWidth="1" transform="rotate(-18 200 200)" />
          <circle cx="378" cy="146" r="3.5" fill="#22d3ee" />
        </svg>
        <svg viewBox="0 0 400 400" className="absolute inset-0 size-full animate-orbit-reverse">
          <ellipse cx="200" cy="200" rx="170" ry="120" fill="none" stroke="#fbbf24" strokeOpacity="0.16" strokeWidth="1" strokeDasharray="2 7" transform="rotate(28 200 200)" />
          <circle cx="58" cy="128" r="2.5" fill="#fbbf24" />
        </svg>
        <svg viewBox="0 0 400 400" className="absolute inset-0 size-full">
          <circle cx="200" cy="200" r="150" fill="none" stroke="#ffffff" strokeOpacity="0.05" />
          <circle cx="200" cy="200" r="104" fill="none" stroke="#ffffff" strokeOpacity="0.04" strokeDasharray="1 5" />
        </svg>

        {/* flame: soot glow -> amber shell -> blue reaction zone -> dark droplet */}
        <div className="absolute inset-[24%] animate-breathe rounded-full bg-[radial-gradient(circle,rgb(251_146_60/0.30)_0%,rgb(251_191_36/0.12)_45%,transparent_70%)] blur-xl" />
        <div className="absolute inset-[31%] animate-breathe rounded-full bg-[radial-gradient(circle,transparent_52%,rgb(56_189_248/0.55)_60%,rgb(251_191_36/0.45)_68%,transparent_76%)]" />
        <div className="absolute inset-[37%] rounded-full bg-[radial-gradient(circle,rgb(224_242_254/0.15)_0%,rgb(56_189_248/0.10)_45%,transparent_70%)]" />
        <div className="absolute inset-[46.5%] rounded-full bg-[radial-gradient(circle_at_35%_35%,#64748b,#0f172a_70%)] shadow-[0_0_24px_rgb(56_189_248/0.45)]" />
      </div>
    </div>
  );
}
