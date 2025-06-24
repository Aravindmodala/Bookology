import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import React, { useState, useRef, useEffect } from "react";

export default function Navbar() {
  const { session, user, signOut } = useAuth();
  const firstName = user?.user_metadata?.first_name || user?.email?.split('@')[0];
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/10 backdrop-blur-md border-b border-white/20 flex items-center justify-between px-8 py-4">
      <div className="text-2xl font-bold tracking-wide text-white">Bookology</div>
      <div className="flex gap-6 items-center">
        <a href="#" className="text-white/80 hover:text-white transition">Home</a>
        <a href="#" className="text-white/80 hover:text-white transition">About</a>
        <a href="#" className="text-white/80 hover:text-white transition">Contact</a>
        <a href="#" className="text-white/80 hover:text-white transition">GitHub</a>
        {session ? (
          <div className="relative" ref={dropdownRef}>
            <button
              className="text-white/80 font-semibold cursor-pointer px-3 py-1 rounded hover:bg-white/20 transition"
              onClick={() => setDropdownOpen((open) => !open)}
            >
              {firstName}
            </button>
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-black border border-white/20 rounded-lg shadow-lg z-50">
                <button
                  className="block w-full text-left px-4 py-2 text-white hover:bg-white/10 transition"
                  onClick={() => { setDropdownOpen(false); alert('Profile details coming soon!'); }}
                >
                  Profile Details
                </button>
                <button
                  className="block w-full text-left px-4 py-2 text-red-400 hover:bg-red-600/20 transition"
                  onClick={() => { setDropdownOpen(false); signOut(); }}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link to="/login" className="text-white/80 hover:text-white transition font-semibold">Login</Link>
        )}
      </div>
    </nav>
  );
} 