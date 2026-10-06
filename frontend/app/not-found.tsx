import { Orbit } from "lucide-react";

import { ButtonLink } from "@/components/ui/button-link";

export default function NotFound() {
  return (
    <main id="main" className="grid min-h-dvh place-items-center px-6 text-center">
      <div className="space-y-5">
        <Orbit className="mx-auto size-10 text-plasma" aria-hidden="true" />
        <p className="label-caps">Error 404</p>
        <h1 className="font-display text-3xl font-semibold">Lost in orbit</h1>
        <p className="text-sm text-ink-2">This page does not exist.</p>
        <ButtonLink href="/dashboard">Back to Mission Control</ButtonLink>
      </div>
    </main>
  );
}
