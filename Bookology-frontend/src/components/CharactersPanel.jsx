import React from 'react';

export default function CharactersPanel({ characters = [] }) {
  if (!characters || characters.length === 0) {
    return (
      <div className="card-soft p-5">
        <div className="text-sm text-off-70 mb-1">Main Characters</div>
        <p className="text-off-60 text-sm">No characters detected yet.</p>
      </div>
    );
  }

  const toArray = (value) => {
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') return value.split(/[,•|-]/).map((s) => s.trim()).filter(Boolean);
    return [];
  };

  return (
    <div className="card-soft p-5">
      <div className="text-sm text-off-70 mb-2">Main Characters</div>
      <div className="space-y-3">
        {characters.map((c, idx) => (
          <div key={idx} className="bg-white/5 border border-white/10 rounded-xl p-3 flex items-start gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-cyan-400 text-black/80 font-semibold flex items-center justify-center shadow-inner">
              {(c?.name?.[0] || c?.title?.[0] || 'C').toUpperCase()}
            </div>
            <div className="min-w-0">
              <div className="font-medium text-off truncate">{c?.name || c?.title || 'Unnamed Character'}</div>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {toArray(c?.traits || c?.attributes).slice(0, 3).map((t, i) => (
                  <span key={i} className="chip text-xs">{t}</span>
                ))}
                {c?.role && <span className="chip text-xs">{c.role}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


