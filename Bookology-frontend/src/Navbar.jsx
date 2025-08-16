import { Link, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import React, { useState, useRef, useEffect } from "react";

export default function Navbar() {
  const { session, user, signOut } = useAuth();
  const location = useLocation();
  const firstName = user?.user_metadata?.first_name || user?.email?.split('@')[0];
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  // DEBUG: Log authentication state
  useEffect(() => {
    console.log('Navbar Auth State:', {
      hasSession: !!session,
      hasUser: !!user,
      firstName,
      dropdownOpen
    });
  }, [session, user, firstName, dropdownOpen]);

  // Close dropdown when clicking outside - FIXED VERSION
  useEffect(() => {
    function handleClickOutside(event) {
      // Check if click is outside both the button and dropdown
      if (
        dropdownRef.current && 
        buttonRef.current &&
        !dropdownRef.current.contains(event.target) &&
        !buttonRef.current.contains(event.target)
      ) {
        console.log('Click outside detected, closing dropdown');
        setDropdownOpen(false);
      }
    }

    // Only add listener when dropdown is open
    if (dropdownOpen) {
      console.log('Adding click outside listener');
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        console.log('Removing click outside listener');
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [dropdownOpen]);

  // Close dropdown on escape key
  useEffect(() => {
    function handleEscapeKey(event) {
      if (event.key === 'Escape' && dropdownOpen) {
        console.log('Escape key pressed, closing dropdown');
        setDropdownOpen(false);
      }
    }

    if (dropdownOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => {
        document.removeEventListener('keydown', handleEscapeKey);
      };
    }
  }, [dropdownOpen]);

  const navLinks = [
    { href: "/", label: "Home", isActive: location.pathname === "/" },
    { href: "#about", label: "About", isActive: false },
    { href: "#contact", label: "Contact", isActive: false },
  ];

  const handleDropdownToggle = (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log('Dropdown toggle clicked, current state:', dropdownOpen);
    setDropdownOpen(prev => {
      const newState = !prev;
      console.log('Dropdown state changed to:', newState);
      return newState;
    });
  };

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
              <div className="relative">
                <button
                  ref={buttonRef}
                  className="flex items-center space-x-2 text-gray-300 hover:text-white px-3 py-2 rounded-md transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
                  onClick={handleDropdownToggle}
                  type="button"
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                  data-testid="profile-dropdown-button"
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

                {/* Dropdown Menu - FIXED VERSION */}
                {dropdownOpen && (
                  <div 
                    ref={dropdownRef}
                    className="absolute right-0 mt-2 w-48 bg-gray-900 border border-gray-700 rounded-xl shadow-2xl z-[9999] animate-slide-in-top"
                    style={{
                      animation: 'slideInFromTop 0.2s ease-out',
                      transformOrigin: 'top right'
                    }}
                    data-testid="profile-dropdown-menu"
                  >
                    <div className="p-2">
                      <div className="px-3 py-2 text-sm text-gray-400 border-b border-gray-700 mb-1">
                        {user?.email}
                      </div>
                      <button
                        className="flex items-center w-full text-left px-3 py-2 text-gray-300 hover:bg-gray-800 hover:text-white rounded-lg transition-all duration-200 focus:outline-none focus:bg-gray-800"
                        onClick={() => { 
                          if (import.meta.env.MODE === 'development') {
                            console.log('Profile details clicked');
                          }
                          setDropdownOpen(false);
                        }}
                        type="button"
                        data-testid="profile-details-button"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Profile Details
                      </button>
                      <button
                        className="flex items-center w-full text-left px-3 py-2 text-red-400 hover:bg-red-900/20 hover:text-red-300 rounded-lg transition-all duration-200 focus:outline-none focus:bg-red-900/20"
                        onClick={() => { 
                          console.log('Sign out clicked');
                          setDropdownOpen(false); 
                          signOut(); 
                        }}
                        type="button"
                        data-testid="sign-out-button"
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