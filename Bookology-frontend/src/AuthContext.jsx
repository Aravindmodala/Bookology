import React, { createContext, useState, useEffect, useContext } from 'react';
import { supabase, isSupabaseEnabled, mockAuth } from './supabaseClient';

const AuthContext = createContext();

// AuthContext.jsx - Bookology Frontend Auth Provider
//
// This file provides React context for authentication state using Supabase Auth.
// It wraps the app and exposes user/session info and signOut to all components.
// Data Flow:
// - On mount, fetches session from Supabase and listens for auth changes.
// - Makes user/session available via useAuth() hook to any component.
//
// (Add or update function-level comments throughout the file)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getSession = async () => {
      try {
        if (isSupabaseEnabled && supabase) {
          const { data: { session } } = await supabase.auth.getSession();
          setSession(session);
          setUser(session?.user ?? null);
        } else {
          // Use mock auth when Supabase is not configured
          console.warn('Supabase not configured, using mock auth for development');
          setSession(null);
          setUser(null);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setSession(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    getSession();

    let authListener = null;
    
    if (isSupabaseEnabled && supabase) {
      const { data } = supabase.auth.onAuthStateChange(
        (event, session) => {
          setSession(session);
          setUser(session?.user ?? null);
          setLoading(false);
        }
      );
      authListener = data;
    }

    return () => {
      if (authListener) {
        authListener.subscription.unsubscribe();
      }
    };
  }, []);

  const value = {
    session,
    user,
    loading,
    isSupabaseEnabled,
    signOut: () => {
      if (isSupabaseEnabled && supabase) {
        return supabase.auth.signOut();
      }
      return Promise.resolve();
    },
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
}; 