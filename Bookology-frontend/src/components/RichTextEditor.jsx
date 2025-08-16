import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TextAlign from '@tiptap/extension-text-align';
import CharacterCount from '@tiptap/extension-character-count';
import { TextStyle } from '@tiptap/extension-text-style';
import Image from '@tiptap/extension-image';
import { Extension } from '@tiptap/core';
import { ReactNodeViewRenderer, NodeViewWrapper } from '@tiptap/react';
import { Selection } from 'prosemirror-state';

// Allow fontSize via TextStyle mark
const FontSize = Extension.create({
  name: 'fontSize',
  addGlobalAttributes() {
    return [
      {
        types: ['textStyle'],
        attributes: {
          fontSize: {
            default: null,
            parseHTML: element => element.style.fontSize || null,
            renderHTML: attributes => {
              if (!attributes.fontSize) return {};
              return { style: `font-size: ${attributes.fontSize}` };
            }
          }
        }
      }
    ];
  }
});

// React NodeView with full Word-like resizing: corners (proportional), sides (independent), delete and exact inputs
const WordLikeImageNode = (props) => {
  const { node, updateAttributes, selected, editor } = props;
  const imgRef = useRef(null);
  const wrapperRef = useRef(null);
  const [hover, setHover] = useState(false);

  const naturalRef = useRef({ w: 0, h: 0, ratio: 1 });
  useEffect(() => {
    const el = imgRef.current;
    if (!el) return;
    const apply = () => (naturalRef.current = { w: el.naturalWidth, h: el.naturalHeight, ratio: (el.naturalWidth || 1) / (el.naturalHeight || 1) });
    if (el.complete && el.naturalWidth) apply(); else el.onload = apply;
  }, []);

  const startRef = useRef({ x: 0, y: 0, w: 0, h: 0, dir: 'e' });
  const onPointerDown = (e, dir) => {
    e.preventDefault();
    e.stopPropagation();
    const img = imgRef.current;
    if (!img) return;
    const rect = img.getBoundingClientRect();
    startRef.current = { x: e.clientX, y: e.clientY, w: rect.width, h: rect.height, dir };
    const onMove = (ev) => {
      const dx = ev.clientX - startRef.current.x;
      const dy = ev.clientY - startRef.current.y;
      const dir = startRef.current.dir;
      const corner = dir.length === 2;
      let newW = startRef.current.w;
      let newH = startRef.current.h;
      const ratio = naturalRef.current.ratio || (startRef.current.w / Math.max(1, startRef.current.h));

      if (corner) {
        // proportional
        const sx = dir.includes('e') ? 1 : -1;
        const sy = dir.includes('s') ? 1 : -1;
        const delta = Math.abs(dx) > Math.abs(dy) ? dx * sx : dy * sy;
        newW = startRef.current.w + delta;
        newH = Math.round(newW / ratio);
      } else {
        if (dir === 'e' || dir === 'w') {
          const sx = dir === 'e' ? 1 : -1;
          newW = startRef.current.w + sx * dx;
          // sides: independent horizontal stretch/compress
        } else if (dir === 's' || dir === 'n') {
          const sy = dir === 's' ? 1 : -1;
          newH = startRef.current.h + sy * dy;
          // sides: independent vertical stretch/compress
        }
      }

      newW = Math.max(50, Math.round(newW));
      newH = Math.max(50, Math.round(newH));
      updateAttributes({ widthPx: newW, heightPx: newH });
    };
    const onUp = () => {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
    };
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  };

  const onDelete = () => {
    try {
      const { state, view } = editor;
      const posGetter = props.getPos;
      const pos = typeof posGetter === 'function' ? posGetter() : null;
      if (typeof pos === 'number') {
        const nodeSize = node.nodeSize || 1;
        let tr = state.tr;
        // Place selection just before the node to keep viewport stable
        const $near = state.doc.resolve(Math.max(0, pos - 1));
        tr = tr.setSelection(Selection.near($near));
        tr = tr.delete(pos, pos + nodeSize);
        view.dispatch(tr);
        view.focus();
      } else {
        editor.commands.deleteSelection();
      }
    } catch {
      editor.commands.deleteSelection();
    }
  };

  const widthPx = node.attrs.widthPx || null;
  const heightPx = node.attrs.heightPx || null;
  const align = node.attrs.align || 'center';
  const styleDim = widthPx || heightPx
    ? { width: widthPx ? `${widthPx}px` : 'auto', height: heightPx ? `${heightPx}px` : 'auto' }
    : { width: '100%', height: 'auto' };
  const alignStyle = (() => {
    if (align === 'left') return { float: 'left', margin: '0.5rem 1rem 0.75rem 0' };
    if (align === 'right') return { float: 'right', margin: '0.5rem 0 0.75rem 1rem' };
    return { display: 'block', margin: '0.75rem auto' };
  })();

  const Handle = ({ pos }) => (
    <div
      onPointerDown={(e) => onPointerDown(e, pos)}
      className={`absolute w-3 h-3 bg-white rounded shadow border border-black/20 ${
        pos.includes('n') ? 'top-0 -translate-y-1/2' : pos.includes('s') ? 'bottom-0 translate-y-1/2' : 'top-1/2 -translate-y-1/2'
      } ${pos.includes('e') ? 'right-0 translate-x-1/2' : pos.includes('w') ? 'left-0 -translate-x-1/2' : 'left-1/2 -translate-x-1/2'} cursor-${
        pos === 'ne' || pos === 'sw' ? 'nesw-resize' : pos === 'nw' || pos === 'se' ? 'nwse-resize' : pos === 'n' || pos === 's' ? 'ns-resize' : 'ew-resize'
      }`} style={{ zIndex: 5 }}
    />
  );

  return (
    <NodeViewWrapper
      as="div"
      ref={wrapperRef}
      className="relative inline-block"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ maxWidth: '100%' }}
    >
      <img
        ref={imgRef}
        src={node.attrs.src}
        alt={node.attrs.alt || ''}
        title={node.attrs.title || ''}
        draggable
        data-drag-handle
        style={{ ...styleDim, ...alignStyle, maxWidth: '100%', cursor: hover || selected ? 'move' : 'default' }}
        className={hover || selected ? 'outline outline-2 outline-violet-400/60' : ''}
      />
      {(hover || selected) && (
        <>
          {/* corners */}
          <Handle pos="nw" />
          <Handle pos="ne" />
          <Handle pos="sw" />
          <Handle pos="se" />
          {/* sides */}
          <Handle pos="n" />
          <Handle pos="s" />
          <Handle pos="e" />
          <Handle pos="w" />
          <button
            onClick={onDelete}
            className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-red-500 text-white text-xs flex items-center justify-center shadow"
            title="Delete image"
            style={{ zIndex: 6 }}
          >
            ×
          </button>
          {/* alignment controls */}
          <div className="absolute -top-9 left-1/2 -translate-x-1/2 flex items-center gap-1 bg-black/55 text-white text-xs rounded px-2 py-1 border border-white/20" style={{ zIndex: 6 }}>
            <button onClick={() => updateAttributes({ align: 'left' })} title="Align left" className={`px-2 py-0.5 rounded ${align==='left' ? 'bg-white/20' : 'hover:bg-white/10'}`}>L</button>
            <button onClick={() => updateAttributes({ align: 'center' })} title="Align center" className={`px-2 py-0.5 rounded ${align==='center' ? 'bg-white/20' : 'hover:bg-white/10'}`}>C</button>
            <button onClick={() => updateAttributes({ align: 'right' })} title="Align right" className={`px-2 py-0.5 rounded ${align==='right' ? 'bg-white/20' : 'hover:bg-white/10'}`}>R</button>
          </div>
        </>
      )}
    </NodeViewWrapper>
  );
};

const WordLikeImage = Image.extend({
  draggable: true,
  addAttributes() {
    return {
      ...this.parent?.(),
      widthPx: {
        default: null,
        parseHTML: element => {
          const style = element.getAttribute('style') || '';
          const m = style.match(/width:\s*(\d+)px/);
          return m ? parseInt(m[1], 10) : null;
        },
        renderHTML: () => ({}),
      },
      heightPx: {
        default: null,
        parseHTML: element => {
          const style = element.getAttribute('style') || '';
          const m = style.match(/height:\s*(\d+)px/);
          return m ? parseInt(m[1], 10) : null;
        },
        renderHTML: () => ({}),
      },
      align: {
        default: 'center',
        parseHTML: element => {
          const style = element.getAttribute('style') || '';
          if (/float:\s*left/.test(style)) return 'left';
          if (/float:\s*right/.test(style)) return 'right';
          return 'center';
        },
        renderHTML: () => ({}),
      },
    };
  },
  renderHTML({ HTMLAttributes }) {
    const base = HTMLAttributes || {};
    const { widthPx, heightPx, align = 'center', style: s, ...rest } = base;
    let style = `${s || ''}; max-width: 100%;`;
    if (align === 'left') style += ' float: left; margin: 0.5rem 1rem 0.75rem 0;';
    else if (align === 'right') style += ' float: right; margin: 0.5rem 0 0.75rem 1rem;';
    else style += ' display: block; margin: 0.75rem auto;';
    if (widthPx) style += ` width: ${widthPx}px;`;
    if (heightPx) style += ` height: ${heightPx}px;`;
    return ['img', { ...rest, style }];
  },
  addNodeView() {
    return ReactNodeViewRenderer(WordLikeImageNode);
  },
});

/**
 * TipTap wrapper component for Bookology editor
 * - Keeps HTML content interface to preserve existing backend endpoints
 * - Exposes selection updates and editor instance readiness to parent
 */
export default function RichTextEditor({
  value,
  onChange,
  disabled,
  onSelectionChange,
  onReady,
  className,
}) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      TextStyle,
      FontSize,
      WordLikeImage.configure({ inline: false, allowBase64: true }),
      CharacterCount,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Placeholder.configure({ placeholder: 'Start writing your story…' }),
    ],
    content: value || '',
    editable: !disabled,
    onUpdate: ({ editor }) => onChange?.(editor.getHTML()),
  });

  // Notify parent when editor is ready
  useEffect(() => {
    if (editor && onReady) onReady(editor);
  }, [editor, onReady]);

  // Keep TipTap content in sync with external HTML value
  useEffect(() => {
    if (!editor) return;
    const html = value || '';
    if (editor.getHTML() !== html) editor.commands.setContent(html, false);
  }, [value, editor]);

  // Update editable state
  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!disabled);
  }, [disabled, editor]);

  // Forward selection updates as plain text
  useEffect(() => {
    if (!editor || !onSelectionChange) return;
    const handler = () => {
      const { from, to } = editor.state.selection;
      const text = editor.state.doc.textBetween(from, to, '\n');
      onSelectionChange(text, { from, to });
    };
    editor.on('selectionUpdate', handler);
    return () => editor.off('selectionUpdate', handler);
  }, [editor, onSelectionChange]);

  return (
    <div className="mx-auto w-full max-w-[920px] px-2 sm:px-3 relative">
      <EditorContent editor={editor} className={className} />
    </div>
  );
}


