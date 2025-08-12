import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

function SectionHeading({ eyebrow, title, subtitle }) {
  return (
    <div className="max-w-4xl mx-auto text-center mb-10">
      {eyebrow && (
        <motion.div
          initial={{ opacity: 0, y: 10, letterSpacing: "0.2em" }}
          whileInView={{ opacity: 1, y: 0, letterSpacing: "0.06em" }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-sm tracking-widest text-off-60 uppercase"
        >
          {eyebrow}
        </motion.div>
      )}
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="font-sora text-4xl md:text-5xl font-semibold text-off"
      >
        {title}
      </motion.h2>
      {subtitle && (
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="mt-4 text-base md:text-lg text-off-70"
        >
          {subtitle}
        </motion.p>
      )}
    </div>
  );
}

export default function LandingPage() {
  const [pricingYearly, setPricingYearly] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, session, signOut } = useAuth();

  const price = (m, y) => (pricingYearly ? y : m);

  const handleStart = () => {
    setIsTransitioning(true);
    // Allow the overlay to animate before navigation for immersive feel
    setTimeout(() => navigate('/create'), 500);
  };

  return (
    <div className="deep-space starfield text-off">
      {/* glow layers */}
      <div className="glow glow-violet" />
      <div className="glow glow-cyan" />

      {/* Header now provided globally via Layout/Header */}

      {/* Hero */}
      <section className="hero container pt-10 pb-16 lg:pt-20 lg:pb-24 grid lg:grid-cols-2 gap-10 items-center">
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="font-sora text-5xl md:text-6xl leading-tight text-off mt-0"
          >
            Write worlds readers can’t put down.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.05 }}
            className="mt-5 text-lg text-off-75 max-w-xl"
          >
            Bookology turns your idea into a cinematic story—chapter by chapter—with perfect continuity.
          </motion.p>

          <div className="mt-7 flex items-center gap-4">
            <button className="btn-violet" onClick={handleStart}>Start a Story</button>
            <a href="#demo" className="btn-outline">Watch Demo</a>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-6 text-off-70">
            <div>10,000+ chapters created</div>
            <span className="opacity-30">|</span>
            <div>Avg. read time 18 min</div>
          </div>
        </div>
        {/* Removed trailer preview per request; keep balanced layout with empty spacer on large screens */}
        <div className="hidden lg:block" />
      </section>

      {/* How It Works */}
      <section id="how" className="container section">
        <SectionHeading
          eyebrow="How it works"
          title="From prompt to polished chapters"
          subtitle="Cinematic momentum with continuity baked in."
        />
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { t: "Prompt", d: "Describe your idea and characters.", k: "📝" },
            { t: "Trailer", d: "Get a short cinematic teaser.", k: "🎬" },
            { t: "Chapter by Chapter", d: "Write interactively with choices.", k: "📖" },
          ].map((c, i) => (
            <motion.div
              key={c.t}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="card-soft h-full"
            >
              <div className="text-3xl">{c.k}</div>
              <div className="mt-3 font-medium text-off">{c.t}</div>
              <div className="mt-1 text-off-70 text-sm">{c.d}</div>
              <div className="progress-dots mt-5" data-index={i} />
            </motion.div>
          ))}
        </div>
      </section>

      {/* For Writers */}
      <section id="writers" className="container section">
        <SectionHeading
          eyebrow="For Writers"
          title="Tools that keep your voice, not replace it"
          subtitle="Control structure, continuity, and style—fast."
        />
        <div className="grid md:grid-cols-2 gap-5">
          {[
            ["Outline to Chapters in Minutes", "Turn outlines into paced chapters."],
            ["Character DNA for Continuity", "Lock traits and relationships."],
            ["Inline Rewrite + Style Controls", "Refine tone, pacing, and POV."],
            ["Art Panels & Covers", "Consistent faces for panels and covers."],
          ].map(([t, d]) => (
            <div key={t} className="card-soft">
              <div className="font-medium text-off">{t}</div>
              <div className="text-off-70 mt-1">{d}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-2xl overflow-hidden border border-white/10 bg-white/5">
          <img
            src="https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=2000&auto=format&fit=crop"
            alt="Writer Workspace"
            className="w-full h-[420px] object-cover opacity-95"
          />
        </div>
      </section>

      {/* For Readers */}
      <section id="readers" className="container section">
        <SectionHeading
          eyebrow="For Readers"
          title="Featured stories"
          subtitle="Swipe through a few worlds we love."
        />
        <div className="carousel">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="story-card">
              <div className="h-40 rounded-xl overflow-hidden mb-3 bg-white/5 border border-white/10">
                <img
                  className="w-full h-full object-cover"
                  src={`https://picsum.photos/seed/bookology-${i}/640/360`}
                  alt="Cover"
                />
              </div>
              <div className="font-medium text-off">The Arc of Night {i + 1}</div>
              <div className="text-sm text-off-70 line-clamp-1">A heist beneath a shattered moon.</div>
              <div className="text-xs text-off-60 mt-1">18 min read</div>
            </div>
          ))}
        </div>
        <div className="mt-5 text-center">
          <Link to="/explore" className="btn-outline">Read Featured</Link>
        </div>
      </section>

      {/* Social Proof */}
      <section className="container section">
        <SectionHeading
          eyebrow="Social Proof"
          title="Loved by writers, readers, and educators"
        />
        <div className="grid md:grid-cols-3 gap-5">
          {[
            ["Writer", "“I outlined and published a serial in a weekend.”"],
            ["Reader", "“Choices make it feel like a show I’m part of.”"],
            ["Educator", "“Great for creative writing and revision.”"],
          ].map(([r, q]) => (
            <div key={r} className="card-soft">
              <div className="text-xs uppercase tracking-widest text-off-60">{r}</div>
              <div className="mt-2 text-off">{q}</div>
            </div>
          ))}
        </div>
        <div className="mt-5 card-soft">
          <div className="text-xs uppercase tracking-widest text-off-60">Case study</div>
          <div className="mt-1 text-off">From prompt to 20k reads in 14 days.</div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="container section">
        <SectionHeading eyebrow="Pricing" title="Pick your pace" />
        <div className="flex items-center justify-center gap-3 mb-6">
          <button
            className={`chip ${!pricingYearly ? "chip-active" : ""}`}
            onClick={() => setPricingYearly(false)}
          >
            Monthly
          </button>
          <button
            className={`chip ${pricingYearly ? "chip-active" : ""}`}
            onClick={() => setPricingYearly(true)}
          >
            Annual <span className="ml-2 text-cyan-300/80">Save 20%</span>
          </button>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            ["Free", price("$0", "$0"), ["Basic writing", "Limited saves", "Community explore"]],
            ["Pro", price("$14", "$11"), ["Unlimited chapters", "DNA continuity", "Rewrite/styles"]],
            ["Studio", price("$39", "$32"), ["Team seats", "Brand art models", "Priority support"]],
          ].map(([name, amt, features]) => (
            <div
              key={name}
              className={`card-soft h-full ${name === "Pro" ? "shadow-violet" : ""}`}
            >
              <div className="font-sora text-xl text-off">{name}</div>
              <div className="mt-2 text-3xl font-semibold text-off">
                {amt}
                <span className="text-base text-off-60 ml-1">
                  {pricingYearly ? "/mo billed yearly" : "/mo"}
                </span>
              </div>
              <ul className="mt-4 space-y-2 text-off-80 text-sm">
                {features.map((f) => (
                  <li key={f}>• {f}</li>
                ))}
              </ul>
              <button className="btn-violet mt-5 w-full" onClick={handleStart}>
                {name === "Free" ? "Start Free" : "Go " + name}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="container section">
        <SectionHeading eyebrow="FAQ" title="Answers to common questions" />
        <div className="space-y-3 max-w-3xl mx-auto">
          {[
            [
              "Do you generate chapters automatically?",
              "No. Chapters are created after you pick from interactive choices.",
            ],
            ["Can I keep my voice?", "Yes. Style controls guide rewrites without overwriting your tone."],
            ["Is there a reader paywall?", "Featured stories are free; optional email gate after chapter 3."],
            ["Can I collaborate?", "Studio plan supports shared workspaces and assets."],
            ["What about images?", "Generate art panels and covers with consistent characters."],
            ["Is my data private?", "We don’t train models on your private projects."],
          ].map(([q, a]) => (
            <details key={q} className="card-soft overflow-hidden">
              <summary className="cursor-pointer text-off font-medium">{q}</summary>
              <div className="pt-2 text-off-75">{a}</div>
            </details>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="container pb-24">
        <div className="rounded-2xl p-8 md:p-10 bg-white/[0.06] border border-white/10 text-center shadow-2xl">
          <h3 className="font-sora text-3xl md:text-4xl text-off">
            Start your first chapter in 60 seconds.
          </h3>
          <p className="text-off-70 mt-2">No credit card required.</p>
          <div className="mt-6">
            <button className="btn-violet" onClick={handleStart}>Start a Story</button>
          </div>
        </div>
      </section>

      {/* Immersive transition overlay */}
      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            className="fixed inset-0 z-[999]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: 'easeInOut' }}
          >
            <div className="absolute inset-0 bg-[#0B0E14]/85" />
            <div className="absolute inset-0" style={{
              background: 'radial-gradient(1200px circle at 50% 50%, rgba(124,58,237,0.4), transparent 60%)'
            }} />
          </motion.div>
        )}
      </AnimatePresence>

      <footer className="container pb-12 text-center text-xs text-off-60">
        © {new Date().getFullYear()} Bookology
      </footer>
    </div>
  );
}


