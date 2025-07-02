// bookologyhome.jsx - Bookology Frontend Home/Landing Page
//
// This file implements the main landing page for Bookology, including hero, how-it-works, demo, genres, and footer.
// It provides navigation to the story generator UI and introduces the app to new users.
// Data Flow:
// - User lands here, can navigate to generator via the Start a Story button.
// - No backend calls are made from this file directly.
//
// (Add or update section/component-level comments throughout the file)
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Navbar from "./Navbar";

// 1. Hero Section
function HeroSection({ onStart }) {
  return (
    <section className="min-h-screen flex items-center justify-center bg-black">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-10 max-w-2xl mx-auto flex flex-col items-center border border-white/20"
      >
        <span className="text-3xl md:text-4xl font-serif text-white mb-6">
          Every great story begins with a whisper...
        </span>
        <button
          onClick={onStart}
          className="mt-8 px-8 py-3 bg-white/20 text-white font-bold rounded-full shadow-lg backdrop-blur-md border border-white/30 hover:bg-white/40 hover:text-black hover:shadow-2xl transition-all text-lg"
        >
          Start a Story
        </button>
      </motion.div>
    </section>
  );
}

// 2. How It Works
function HowItWorks() {
  const steps = [
    { icon: "✍️", title: "Type your idea" },
    { icon: "🧠", title: "Bookology expands it into a world" },
    { icon: "📖", title: "You get Chapter 1, instantly" },
  ];
  return (
    <section className="py-20 bg-black">
      <div className="flex flex-col md:flex-row justify-center gap-8 max-w-4xl mx-auto">
        {steps.map((step, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.05 }}
            className="flex-1 bg-white/10 backdrop-blur-lg rounded-2xl p-8 text-center shadow-lg border border-white/20"
          >
            <div className="text-4xl mb-4">{step.icon}</div>
            <div className="text-xl font-semibold text-white">{step.title}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

// 3. Live Demo Preview
function LiveDemoPreview() {
  return (
    <section className="py-20 flex flex-col items-center bg-black">
      <motion.div
        whileHover={{ scale: 1.03 }}
        className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-xl border border-white/20 max-w-xl w-full text-center"
      >
        <div className="text-lg text-white/80 mb-4 animate-pulse">
          <span className="italic">A girl trapped in a city where silence is law…</span>
        </div>
        <motion.div
          whileTap={{ scale: 0.98 }}
          className="mt-6 cursor-pointer bg-white/20 rounded-xl p-6 text-white/70 blur-sm hover:blur-none transition-all duration-300"
        >
          <span className="font-serif">Tap to Reveal</span>
        </motion.div>
      </motion.div>
    </section>
  );
}

// 4. Genre Carousel
function GenreCarousel() {
  const genres = [
    { name: "Sci-Fi" },
    { name: "Romance" },
    { name: "Thriller" },
    { name: "Mythological Fantasy" },
    { name: "Dark Academia" },
  ];
  return (
    <section className="py-20 bg-black">
      <div className="flex gap-6 justify-center flex-wrap">
        {genres.map((g, i) => (
          <motion.div
            key={g.name}
            whileHover={{ scale: 1.08 }}
            className={
              "w-48 h-64 bg-white/10 backdrop-blur-lg rounded-3xl shadow-xl flex items-center justify-center text-2xl font-bold text-white cursor-pointer border border-white/20 transition-transform duration-300"
            }
            style={{ perspective: 1000 }}
          >
            {g.name}
          </motion.div>
        ))}
      </div>
    </section>
  );
}

// 5. Quote Section
function QuoteSection() {
  return (
    <section className="relative py-20 bg-black">
      <div className="absolute inset-0 bg-white/5 backdrop-blur-sm z-0" />
      <div className="relative z-10 flex flex-col items-center">
        <motion.blockquote
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2 }}
          className="text-2xl md:text-3xl font-serif text-white text-center max-w-2xl"
        >
          “There is no greater agony than bearing an untold story inside you.”
          <span className="block mt-4 text-lg text-white/60">– Maya Angelou</span>
        </motion.blockquote>
      </div>
    </section>
  );
}

// 6. Footer
function Footer() {
  return (
    <footer className="bg-white/10 backdrop-blur-lg border-t border-white/20 py-6 flex flex-col md:flex-row items-center justify-between px-8 text-white/80">
      <div className="flex gap-6 mb-4 md:mb-0">
        <a href="#" className="hover:text-white/100 transition">About</a>
        <a href="#" className="hover:text-white/100 transition">Contact</a>
        <a href="#" className="hover:text-white/100 transition">GitHub</a>
        <a href="#" className="hover:text-white/100 transition">Privacy</a>
      </div>
      <div className="flex items-center gap-4">
        <button className="bg-white/20 px-3 py-1 rounded-full shadow hover:bg-white/30 transition">🔊 Ambient</button>
        <select className="bg-white/20 px-3 py-1 rounded-full shadow text-white/80">
          <option>EN</option>
          <option>ES</option>
          <option>FR</option>
        </select>
      </div>
    </footer>
  );
}

// Main Home Component
export default function BookologyHome({ onStart }) {
  const { isSupabaseEnabled } = useAuth();
  
  return (
    <div className="min-h-screen w-screen bg-black text-white font-serif">
      <Navbar />
      {/* Development Notice */}
      {!isSupabaseEnabled && (
        <div className="bg-yellow-600/20 border border-yellow-500/50 text-yellow-200 px-4 py-2 text-center text-sm">
          ⚠️ Development Mode: Supabase not configured. Some features may be limited.
        </div>
      )}
      <div className="pt-24">
        <HeroSection onStart={onStart} />
        <HowItWorks />
        <LiveDemoPreview />
        <GenreCarousel />
        <QuoteSection />
        <Footer />
      </div>
    </div>
  );
}
