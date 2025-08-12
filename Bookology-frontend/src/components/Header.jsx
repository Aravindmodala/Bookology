import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

function Brand() {
  return (
    <Link to="/" className="logo-roman text-off-90 text-xl">
      BOOKOLOGY
    </Link>
  );
}

function AvatarMenu() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!user) return null;

  return (
    <div
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        className="w-9 h-9 rounded-full bg-white/10 border border-white/15 text-off font-semibold flex items-center justify-center hover:bg-white/15"
        aria-haspopup="true"
        aria-expanded={open}
      >
        {(user?.email?.[0] || 'U').toUpperCase()}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl border border-white/10 bg-[#0E131B] shadow-2xl overflow-hidden z-50">
          <div className="px-4 py-3 text-sm text-off-70 border-b border-white/10">{user?.email}</div>
          <button className="w-full text-left px-4 py-2 text-off hover:bg-white/5" onClick={() => navigate('/stories')}>Dashboard</button>
          <button className="w-full text-left px-4 py-2 text-off hover:bg-white/5" onClick={() => navigate('/create')}>Create New</button>
          <button className="w-full text-left px-4 py-2 text-off hover:bg-white/5" onClick={() => navigate('/editor')}>Open Editor</button>
          <div className="border-t border-white/10" />
          <button className="w-full text-left px-4 py-2 text-red-300 hover:bg-red-500/10" onClick={signOut}>Sign out</button>
        </div>
      )}
    </div>
  );
}

export default function Header({ variant = 'default' }) {
  const { session } = useAuth();

  if (variant === 'minimal') {
    return (
      <div className="fixed top-0 inset-x-0 z-50 bg-black/30 backdrop-blur-md">
        <div className="container py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Brand />
            <Link to="/stories" className="btn-ghost-soft text-sm">Back to Stories</Link>
          </div>
          <div className="flex items-center gap-3">
            {/* Save status placeholder could be inserted here */}
            {session ? <AvatarMenu /> : <Link to="/login" className="btn-ghost-soft text-sm">Sign in</Link>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <header className="site-header fixed top-0 inset-x-0 z-50 bg-white/5 backdrop-blur-md">
      <div className="container py-4 flex items-center justify-between">
        <Brand />
        <nav className="hidden md:flex items-center gap-6 text-sm nav-roman">
          <a href="#how" className="nav-soft">How it works</a>
          <a href="#pricing" className="nav-soft">Pricing</a>
          <Link to="/explore" className="nav-soft">Explore</Link>
        </nav>
        <div className="flex items-center gap-3 relative">
          {!session ? (
            <Link to="/login" className="btn-ghost-soft">Sign in</Link>
          ) : (
            <AvatarMenu />
          )}
        </div>
      </div>
    </header>
  );
}


