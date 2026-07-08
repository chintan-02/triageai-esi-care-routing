import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { MobileNav } from './MobileNav';

export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-clinical-surface text-slate-900">
      <div className="flex min-h-screen">
        <Sidebar />
        <MobileNav open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onOpenMenu={() => setMobileNavOpen(true)} />
          <main className="flex-1">
            <div className="clinical-grid min-h-[calc(100vh-76px)] px-4 pb-8 pt-5 sm:px-6 sm:pt-6 lg:px-8 lg:pt-8">
              <div className="mx-auto w-full max-w-7xl">
                <Outlet />
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
