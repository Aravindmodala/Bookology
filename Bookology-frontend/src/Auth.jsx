// Auth.jsx - Bookology Frontend Auth UI
//
// This file implements the login and signup forms for Bookology, using Supabase Auth for authentication.
// It uses AuthContext to get/set auth state and redirects users after login/signup.
// Data Flow:
// - User enters credentials or uses social login.
// - Calls Supabase Auth methods to sign in/up.
// - On success, updates AuthContext and redirects to the main app.
//
import React, { useState, useEffect } from 'react'
import { supabase, isSupabaseEnabled } from './supabaseClient'
import { useAuth } from './AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Auth() {
  const { session, loading } = useAuth();
  const navigate = useNavigate();

  // Debug: Log session and loading state
  console.log('Auth.jsx - session:', session);
  console.log('Auth.jsx - loading:', loading);

  // Debug: Force sign out on mount to clear any stale session
  useEffect(() => {
    if (isSupabaseEnabled && supabase) {
      supabase.auth.signOut().then(() => {
        console.log('Forced sign out on mount (debug)');
      });
    }
  }, []);

  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    console.log('useEffect - session:', session, 'loading:', loading);
    if (!loading && session) {
      console.log('Redirecting to / because session exists');
      navigate('/');
    }
  }, [session, loading, navigate]);
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setFormLoading(true);
    
    if (!isSupabaseEnabled || !supabase) {
      setError('Authentication is not configured. Please check your environment variables.');
      setFormLoading(false);
      return;
    }
    
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setError(error.message);
    setFormLoading(false);
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match!');
      return;
    }
    
    if (!isSupabaseEnabled || !supabase) {
      setError('Authentication is not configured. Please check your environment variables.');
      setFormLoading(false);
      return;
    }
    
    setFormLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) setError(error.message);
    else setError('Sign up successful! Please check your email to verify your account.');
    setFormLoading(false);
  };

  // Add social login handler
  const signInWithProvider = async (provider) => {
    setFormLoading(true);
    
    if (!isSupabaseEnabled || !supabase) {
      setError('Authentication is not configured. Please check your environment variables.');
      setFormLoading(false);
      return;
    }
    
    const { error } = await supabase.auth.signInWithOAuth({ provider });
    if (error) setError(error.message);
    setFormLoading(false);
  };

  return (
    <div className="min-h-screen w-screen bg-black flex items-center justify-center">
      {/* Development Notice */}
      {!isSupabaseEnabled && (
        <div className="absolute top-0 left-0 right-0 bg-yellow-600/20 border-b border-yellow-500/50 text-yellow-200 px-4 py-2 text-center text-sm">
          ⚠️ Development Mode: Authentication not configured. Please set up Supabase environment variables.
        </div>
      )}
      <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-10 w-full max-w-md border border-white/20 flex flex-col items-center">
        <h1 className="text-4xl font-serif font-bold text-white mb-4">
          {isSignUp ? 'Sign Up' : 'Login'}
        </h1>
        {/* Social Logins - only show on login, not sign up */}
        {!isSignUp && (
          <div className="w-full flex flex-col gap-4 mb-6">
            <button
              onClick={() => signInWithProvider('google')}
              className="w-full py-3 rounded-full bg-red-600/80 text-white font-bold shadow hover:bg-red-700 transition-all border border-red-500"
              disabled={formLoading}
            >
              {formLoading ? <span>Loading...</span> : <span>Login with Google</span>}
            </button>
            <button
              onClick={() => signInWithProvider('facebook')}
              className="w-full py-3 rounded-full bg-blue-600/80 text-white font-bold shadow hover:bg-blue-700 transition-all border border-blue-500"
              disabled={formLoading}
            >
              {formLoading ? <span>Loading...</span> : <span>Login with Facebook</span>}
            </button>
          </div>
        )}
        <p className="text-white/60 mb-6">
          {isSignUp ? 'Fill in the details to get started' : 'Sign in to continue'}
        </p>
        
        {/* Development Mode Bypass */}
        {!isSupabaseEnabled && (
          <div className="w-full mb-6">
            <button
              onClick={() => {
                console.log('Development mode: bypassing authentication');
                navigate('/');
              }}
              className="w-full py-3 rounded-full bg-green-600/80 text-white font-bold shadow hover:bg-green-700 transition-all border border-green-500"
            >
              🚀 Continue in Development Mode
            </button>
            <p className="text-xs text-white/50 text-center mt-2">
              Skip authentication for development/testing
            </p>
          </div>
        )}
        
        <div className="relative w-full my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/20" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-black text-white/60">
              Or continue with email
            </span>
          </div>
        </div>
        
        <form onSubmit={isSignUp ? handleSignUp : handleLogin} className="w-full flex flex-col gap-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-black/40 text-white placeholder-white/60 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/30"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full px-4 py-3 rounded-lg bg-black/40 text-white placeholder-white/60 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/30"
            required
          />
          {isSignUp && (
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-black/40 text-white placeholder-white/60 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/30"
              required
            />
          )}
          <button
            type="submit"
            className="w-full py-3 rounded-full bg-white/20 text-white font-bold shadow hover:bg-white/40 hover:text-black transition-all border border-white/30"
            disabled={formLoading}
          >
            {formLoading ? (isSignUp ? 'Signing Up...' : 'Logging In...') : (isSignUp ? 'Sign Up' : 'Login')}
          </button>
        </form>

        {error && <div className="text-red-400 mt-4 text-center">{error}</div>}

        <p className="text-white/60 mt-6">
          {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            onClick={() => { setIsSignUp(!isSignUp); setError(''); }}
            className="font-semibold text-white hover:underline"
          >
            {isSignUp ? 'Login' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  )
} 