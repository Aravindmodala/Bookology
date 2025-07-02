import { Link, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import React, { useState, useRef, useEffect } from "react";

export default function Navbar() {
  const { session, user, signOut } = useAuth();
  const location = useLocation();
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

  const navLinks = [
    { href: "/", label: "Home", isActive: location.pathname === "/" },
    { href: "/generator", label: "Generator", isActive: location.pathname === "/generator" },
    { href: "#about", label: "About", isActive: false },
    { href: "#contact", label: "Contact", isActive: false },
  ];

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-black/90 backdrop-blur-md border-b border-gray-800">
      <div className="container">
        <div className="flex items-center justify-between py-4">
          {/* Logo */}
          <Link to="/" className="text-2xl font-bold text-white hover:text-gray-200 transition-colors">
            📚 Bookology
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={`nav-link ${link.isActive ? 'active' : ''}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {session ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  className="flex items-center space-x-2 text-gray-300 hover:text-white px-3 py-2 rounded-md transition-all duration-300"
                  onClick={() => setDropdownOpen((open) => !open)}
                >
                  <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-sm font-medium">
                    {firstName?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <span className="hidden sm:block font-medium">{firstName}</span>
                  <svg 
                    className={`w-4 h-4 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-50 animate-slide-in-top">
                    <div className="p-2">
                      <div className="px-3 py-2 text-sm text-gray-400 border-b border-gray-700 mb-1">
                        {user?.email}
                      </div>
                      <button
                        className="flex items-center w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-800 hover:text-white rounded-lg transition-all duration-200"
                        onClick={() => { 
                          setDropdownOpen(false); 
                          alert('Profile details coming soon!'); 
                        }}
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Profile Details
                      </button>
                      <button
                        className="flex items-center w-full text-left px-3 py-2 text-red-400 hover:bg-red-900/20 hover:text-red-300 rounded-lg transition-all duration-200"
                        onClick={() => { 
                          setDropdownOpen(false); 
                          signOut(); 
                        }}
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link 
                to="/login" 
                className="btn-primary text-sm px-4 py-2"
              >
                Get Started
              </Link>
            )}

            {/* Mobile Menu Button */}
            <button className="md:hidden btn-icon">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
} 