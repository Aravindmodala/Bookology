import React, { useEffect, useId, useMemo, useState } from 'react';
import { Sparkles, ChevronDown, Zap, Type, MessageSquare, Lightbulb, Repeat } from 'lucide-react';

function AssistantPanel({ isForcedClosed, onContinue, onImprove, onDialogue, onBrainstorm, onRewriteChapter }) {
  const panelId = useId();
  const [open, setOpen] = useState(false);

  // Default: open on >=1280px, closed otherwise
  useEffect(() => {
    const prefersOpen = typeof window !== 'undefined' && window.matchMedia('(min-width: 1280px)').matches;
    setOpen(prefersOpen);
  }, []);

  const actuallyOpen = open && !isForcedClosed;

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-[0_8px_40px_rgba(0,0,0,0.45)]">
      <button
        type="button"
        className="w-full px-4 py-3 flex items-center justify-between text-slate-100 hover:bg-white/10 rounded-2xl focus:outline-none focus:ring-2 focus:ring-sky-300/40"
        aria-expanded={actuallyOpen}
        aria-controls={panelId}
        onClick={() => setOpen(v => !v)}
      >
        <span className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-300" />
          <span className="font-medium">AI Assistant</span>
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${actuallyOpen ? 'rotate-180' : ''}`} />
      </button>

      <div
        id={panelId}
        className={`overflow-hidden transition-[max-height,opacity] duration-300 ease-out ${actuallyOpen ? 'max-h-[480px] opacity-100' : 'max-h-0 opacity-0 pointer-events-none'}`}
      >
        <div className="p-3 space-y-2">
          <button onClick={onContinue} className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:translate-y-[1px] transition flex items-center gap-2">
            <Zap className="w-4 h-4 text-violet-300" />
            <span>Continue Chapter</span>
          </button>
          <button onClick={onImprove} className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:translate-y-[1px] transition flex items-center gap-2">
            <Type className="w-4 h-4 text-violet-300" />
            <span>Improve Writing</span>
          </button>
          <button onClick={onDialogue} className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:translate-y-[1px] transition flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-violet-300" />
            <span>Add Dialogue</span>
          </button>
          <button onClick={onBrainstorm} className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:translate-y-[1px] transition flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-violet-300" />
            <span>Brainstorm Ideas</span>
          </button>
          <button onClick={onRewriteChapter} className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:translate-y-[1px] transition flex items-center gap-2">
            <Repeat className="w-4 h-4 text-violet-300" />
            <span>Rewrite Chapter</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// QuickActions removed per UX consolidation

export default function RightSidebar({
  focusCollapsed = false,
  onContinue,
  onImprove,
  onDialogue,
  onBrainstorm,
  onRewriteChapter
}) {
  return (
    <div className={`w-[320px] border-l border-white/10 p-4 overflow-y-auto no-scrollbar ${focusCollapsed ? 'hidden xl:block opacity-0 scale-95 translate-y-1' : ''}`}>
      <AssistantPanel
        isForcedClosed={focusCollapsed}
        onContinue={onContinue}
        onImprove={onImprove}
        onDialogue={onDialogue}
        onBrainstorm={onBrainstorm}
        onRewriteChapter={onRewriteChapter}
      />
    </div>
  );
}


