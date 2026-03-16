import type { PropsWithChildren } from "react";

import { Footer } from "./Footer";
import { MainNav } from "./MainNav";

export function SiteShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(32,82,204,0.10),_transparent_28%),_linear-gradient(180deg,_rgba(255,255,255,0.02),_rgba(255,255,255,0))]">
      <MainNav />
      <main>{children}</main>
      <Footer />
    </div>
  );
}
