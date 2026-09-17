import { Outlet, Link } from 'react-router-dom';
import { Rocket } from 'lucide-react';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-surface sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="bg-primary/20 p-2 rounded-lg">
              <Rocket className="w-6 h-6 text-primary" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">ResearchPilot</span>
          </Link>
          <nav className="flex gap-6">
            <Link to="/" className="text-sm font-medium text-textSecondary hover:text-white transition-colors">
              New Research
            </Link>
            <Link to="/tasks" className="text-sm font-medium text-textSecondary hover:text-white transition-colors">
              Task Board
            </Link>
          </nav>
        </div>
      </header>
      
      <main className="flex-1 max-w-7xl mx-auto px-4 py-8 w-full">
        <Outlet />
      </main>
    </div>
  );
}
