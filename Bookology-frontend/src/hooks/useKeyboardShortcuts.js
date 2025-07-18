import { useEffect } from 'react';

const useKeyboardShortcuts = ({ 
  onSave, 
  onUndo, 
  onRedo, 
  onBold, 
  onItalic, 
  onUnderline,
  onFind,
  onContinueWriting 
}) => {
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Check if Ctrl (or Cmd on Mac) is pressed
      const isCtrl = event.ctrlKey || event.metaKey;
      
      if (isCtrl) {
        switch (event.key.toLowerCase()) {
          case 's':
            event.preventDefault();
            onSave?.();
            break;
          case 'z':
            if (event.shiftKey) {
              event.preventDefault();
              onRedo?.();
            } else {
              event.preventDefault();
              onUndo?.();
            }
            break;
          case 'y':
            event.preventDefault();
            onRedo?.();
            break;
          case 'b':
            event.preventDefault();
            onBold?.();
            break;
          case 'i':
            event.preventDefault();
            onItalic?.();
            break;
          case 'u':
            event.preventDefault();
            onUnderline?.();
            break;
          case 'f':
            event.preventDefault();
            onFind?.();
            break;
          case 'enter':
            event.preventDefault();
            onContinueWriting?.();
            break;
          default:
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onSave, onUndo, onRedo, onBold, onItalic, onUnderline, onFind, onContinueWriting]);
};

export default useKeyboardShortcuts; 