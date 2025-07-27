import React from 'react';
import { useEditorStore } from '../store/editorStore';
import { Gamepad2, BookOpen } from 'lucide-react';

export default function GameModeToggle({ disabled = false }) {
  const { gameMode, setGameMode } = useEditorStore();

  const handleToggle = () => {
    if (!disabled) {
      setGameMode(!gameMode);
    }
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg border border-gray-200">
      {/* Normal Mode Label */}
      <div className={`flex items-center gap-1 text-sm transition-colors ${
        !gameMode 
          ? 'text-blue-600 font-semibold' 
          : 'text-gray-500'
      }`}>
        <BookOpen size={14} />
        <span>Normal</span>
      </div>

      {/* Toggle Switch */}
      <button
        onClick={handleToggle}
        disabled={disabled}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          disabled 
            ? 'opacity-50 cursor-not-allowed bg-gray-400' 
            : gameMode 
              ? 'bg-blue-600' 
              : 'bg-gray-300'
        }`}
        role="switch"
        aria-checked={gameMode}
        aria-label={`Switch to ${gameMode ? 'Normal' : 'Game'} mode`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform ${
            gameMode 
              ? 'translate-x-6' 
              : 'translate-x-1'
          }`}
        />
      </button>

      {/* Game Mode Label */}
      <div className={`flex items-center gap-1 text-sm transition-colors ${
        gameMode 
          ? 'text-blue-600 font-semibold' 
          : 'text-gray-500'
      }`}>
        <Gamepad2 size={14} />
        <span>Game</span>
      </div>
    </div>
  );
} 