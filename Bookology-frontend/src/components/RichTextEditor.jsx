import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TextAlign from '@tiptap/extension-text-align';
import CharacterCount from '@tiptap/extension-character-count';
import { TextStyle } from '@tiptap/extension-text-style';
import Image from '@tiptap/extension-image';
import Gapcursor from '@tiptap/extension-gapcursor';
import Focus from '@tiptap/extension-focus';
import DragHandle from '@tiptap/extension-drag-handle';
import { Extension } from '@tiptap/core';
import { ReactNodeViewRenderer, NodeViewWrapper } from '@tiptap/react';
import { Selection, Plugin, PluginKey } from 'prosemirror-state';

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

  const [isResizing, setIsResizing] = useState(false);
  const startRef = useRef({ x: 0, y: 0, w: 0, h: 0, dir: 'e', lastTs: 0 });
  const onPointerDown = (e, dir) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    const img = imgRef.current;
    if (!img) return;
    const rect = img.getBoundingClientRect();
    startRef.current = { x: e.clientX, y: e.clientY, w: rect.width, h: rect.height, dir, lastTs: 0 };
    const onMove = (ev) => {
      // throttle to ~60fps for smoothness
      const now = performance.now();
      if (startRef.current.lastTs && now - startRef.current.lastTs < 14) return;
      startRef.current.lastTs = now;
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

      newW = Math.max(60, Math.round(newW));
      newH = Math.max(60, Math.round(newH));
      requestAnimationFrame(() => updateAttributes({ widthPx: newW, heightPx: newH }));
    };
    const onUp = () => {
      setIsResizing(false);
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
      className={`absolute w-3.5 h-3.5 rounded-full shadow-md border transition-transform duration-150 bg-gradient-to-br from-blue-500 to-indigo-600 border-white ${
        pos.includes('n') ? 'top-0 -translate-y-1/2' : pos.includes('s') ? 'bottom-0 translate-y-1/2' : 'top-1/2 -translate-y-1/2'
      } ${pos.includes('e') ? 'right-0 translate-x-1/2' : pos.includes('w') ? 'left-0 -translate-x-1/2' : 'left-1/2 -translate-x-1/2'} hover:scale-110 cursor-${
        pos === 'ne' || pos === 'sw' ? 'nesw-resize' : pos === 'nw' || pos === 'se' ? 'nwse-resize' : pos === 'n' || pos === 's' ? 'ns-resize' : 'ew-resize'
      }`} style={{ zIndex: 8 }}
    />
  );

  const [isDragging, setIsDragging] = useState(false);
  const onDragStart = (e) => {
    try {
      e.dataTransfer.effectAllowed = 'move';
      // custom ghost
      const img = imgRef.current;
      if (img) {
        const ghost = img.cloneNode(true);
        ghost.style.position = 'absolute';
        ghost.style.top = '-10000px';
        ghost.style.left = '-10000px';
        ghost.style.opacity = '0.8';
        ghost.style.transform = 'rotate(1.5deg) scale(0.9)';
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, ghost.width / 2, ghost.height / 2);
        setTimeout(() => ghost.remove(), 0);
      }
      setIsDragging(true);
    } catch {}
  };
  const onDragEnd = () => setIsDragging(false);

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
        draggable={true}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        data-drag-handle
        style={{ ...styleDim, ...alignStyle, maxWidth: '100%', cursor: isDragging ? 'grabbing' : (hover || selected ? 'grab' : 'default'), opacity: isDragging ? 0.6 : 1, transition: 'opacity 160ms ease, transform 160ms ease', transform: isDragging ? 'scale(0.98)' : 'scale(1)' }}
        className={`${hover || selected ? 'outline outline-2 outline-violet-400/60' : ''} ${isResizing ? 'select-none' : ''}`}
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
  addProseMirrorPlugins() {
    const key = new PluginKey('wordLikeImageDnD');
    let dragFromPos = null;
    // Drop indicator disabled for cleaner drag UI
    const showIndicatorAt = () => {};
    const hideIndicator = () => {};

    return [
      new Plugin({
        key,
        props: {
          handleDOMEvents: {
            dragstart(view, event) {
              const target = event.target;
              const img = target && target.closest && target.closest('img');
              if (!img) return false;
              const pos = view.posAtDOM(img, 0);
              dragFromPos = pos;
              return false;
            },
            dragover(view, event) {
              if (dragFromPos == null) return false;
              event.preventDefault();
              const coords = { left: event.clientX, top: event.clientY };
              const pos = view.posAtCoords(coords);
              if (pos && pos.pos != null) {
                const box = view.coordsAtPos(pos.pos);
                showIndicatorAt({ top: box.top });
              }
              return true;
            },
            drop(view, event) {
              if (dragFromPos == null) return false;
              hideIndicator();
              event.preventDefault();
              const result = view.posAtCoords({ left: event.clientX, top: event.clientY });
              if (!result || result.pos == null) { dragFromPos = null; return true; }
              let dropPos = result.pos;
              // Prevent no-op/self drop nearby
              if (Math.abs(dropPos - dragFromPos) < 2) { dragFromPos = null; return true; }

              // Resolve the node at dragFromPos
              const $from = view.state.doc.resolve(dragFromPos);
              const node = $from.nodeAfter || $from.nodeBefore;
              if (!node) { dragFromPos = null; return true; }

              // If moving forward past the removed position, account for deletion shift
              if (dropPos > dragFromPos) {
                dropPos -= node.nodeSize || 1;
              }

              const tr = view.state.tr;
              tr.delete(dragFromPos, dragFromPos + (node.nodeSize || 1));
              tr.insert(dropPos, node.type.create(node.attrs));
              view.dispatch(tr);
              view.focus();
              dragFromPos = null;
              return true;
            },
            dragend() {
              hideIndicator();
              dragFromPos = null;
              return false;
            },
          },
        },
      })
    ];
  },
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
  const wrapperRef = useRef(null);
  const [hoverAnchor, setHoverAnchor] = useState(null); // { el: HTMLElement, rect: DOMRect }
  const [showPopover, setShowPopover] = useState(false);
  const popoverHoverRef = useRef(false);
  const editor = useEditor({
    extensions: [
      // Disable built-ins so we can provide tuned versions below
      StarterKit.configure({
        dropcursor: false,
        gapcursor: false,
      }),
      TextStyle,
      FontSize,
      WordLikeImage.configure({ inline: false, allowBase64: false }),
      CharacterCount,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Placeholder.configure({ placeholder: 'Start writing your story…' }),
      // Performance/UX enhancements
      // Dropcursor removed to avoid blue drop line during drags
      Gapcursor,
      Focus.configure({ className: 'has-focus', mode: 'all' }),
      DragHandle.configure({
        // Show a handle for block nodes including images for precise dragging
        // Defaults are fine; extension detects nodes with draggable spec
      }),
    ],
    content: value || '',
    editable: !disabled,
    onUpdate: ({ editor }) => onChange?.(editor.getHTML()),
  });

  // Keep the paragraph arrow anchored to the current selection (static presence)
  useEffect(() => {
    if (!editor) return;
    const setFromSelection = () => {
      try {
        const { from } = editor.state.selection;
        const domPos = editor.view.domAtPos(from);
        const baseEl = domPos && domPos.node ? (domPos.node.nodeType === 1 ? domPos.node : domPos.node.parentElement) : null;
        if (!baseEl) return;
        const para = baseEl.closest && baseEl.closest('p');
        if (!para || !editor.view.dom.contains(para)) return;
        const rect = para.getBoundingClientRect();
        setHoverAnchor({ el: para, rect });
      } catch {}
    };
    editor.on('selectionUpdate', setFromSelection);
    setFromSelection();
    return () => editor.off('selectionUpdate', setFromSelection);
  }, [editor]);

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
    <div
      ref={wrapperRef}
      className="mx-auto w-full max-w-[920px] px-2 sm:px-3 relative"
      onMouseLeave={() => { setShowPopover(false); }}
    >
      {/* global drop indicator bar */}
      <div id="drop-indicator" style={{position:'fixed',left:0,top:0,height:'2px',background:'rgb(59,130,246)',display:'none',zIndex:9999}} />
      <EditorContent
        editor={editor}
        className={className}
        onMouseMove={(e) => {
          try {
            const root = wrapperRef.current;
            if (!root || !editor?.view?.dom) return;
            const pm = editor.view.dom;
            let target = e.target;
            if (!(target instanceof Element)) return;
            // Find closest paragraph inside ProseMirror
            const para = target.closest('p');
            // Do not clear anchor when mouse leaves paragraph area; keep static arrow
            if (!para || !pm.contains(para)) { return; }
            const rect = para.getBoundingClientRect();
            setHoverAnchor({ el: para, rect });
          } catch {}
        }}
        onMouseLeave={() => { /* keep anchor while interacting with the arrow/popover */ }}
      />

      {/* Paragraph-side arrow affordance */}
      {hoverAnchor && (
        <div
          style={{
            position: 'absolute',
            top: `${Math.max(0, (hoverAnchor.rect.top - (wrapperRef.current?.getBoundingClientRect()?.top || 0)) + 2)}px`,
            // Fix: position arrow relative to editor content left edge to keep it visible
            left: `-24px`,
            zIndex: 20,
          }}
          onMouseEnter={() => { popoverHoverRef.current = true; setShowPopover(true); }}
          onMouseLeave={() => { popoverHoverRef.current = false; setShowPopover(false); }}
        >
          <button
            type="button"
            aria-label="Paragraph actions"
            className="w-6 h-6 bg-transparent text-white/70 hover:text-white text-sm leading-6 text-center"
          >
            ›
          </button>

          {showPopover && (
            <div className="mt-1 ml-6 rounded-lg bg-white/95 backdrop-blur text-black text-sm shadow-lg border border-black/10 overflow-hidden" role="menu"
                 onMouseEnter={() => { popoverHoverRef.current = true; }}
                 onMouseLeave={() => { popoverHoverRef.current = false; setShowPopover(false); }}>
              <button
                className="block w-full text-left px-3 py-2 hover:bg-black/5"
                onClick={() => {
                  // Placeholder for future AI flow
                  setShowPopover(false);
                }}
              >
                Create Image
              </button>
              <button
                className="block w-full text-left px-3 py-2 hover:bg-black/5"
                onClick={() => {
                  try {
                    setShowPopover(false);
                    const para = hoverAnchor?.el;
                    const view = editor?.view;
                    if (!para || !view) return;
                    const posAfter = view.posAtDOM(para, para.childNodes.length || 0);
                    // File picker
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.accept = 'image/png,image/jpeg,image/webp';
                    input.onchange = async () => {
                      const file = input.files?.[0];
                      if (!file) return;
                      
                      // Auto-generate alt text from filename (optional)
                      const alt = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
                      
                      try {
                        // Import Supabase client
                        const { supabase } = await import('../supabaseClient.js');
                        if (!supabase) {
                          console.warn('Supabase not configured, falling back to base64');
                          // Fallback to base64 if Supabase not available
                          const reader = new FileReader();
                          reader.onload = () => {
                            const src = String(reader.result || '');
                            editor.chain().focus().insertContentAt(posAfter, [
                              { type: 'image', attrs: { src, alt } },
                            ]).run();
                          };
                          reader.readAsDataURL(file);
                          return;
                        }
                        
                        // Upload to Supabase Storage
                        const timestamp = Date.now();
                        const path = `editor-images/${timestamp}-${file.name}`;
                        
                        const { error: uploadError } = await supabase.storage
                          .from('editor-assets')
                          .upload(path, file, {
                            cacheControl: '3600',
                            upsert: true,
                          });
                        
                        if (uploadError) {
                          console.error('Upload failed:', uploadError);
                          return;
                        }
                        
                        // Get public URL
                        const { data: urlData } = supabase.storage
                          .from('editor-assets')
                          .getPublicUrl(path);
                        
                        const src = urlData?.publicUrl;
                        if (!src) {
                          console.error('Failed to get public URL');
                          return;
                        }
                        
                        // Insert image with Supabase URL
                        editor.chain().focus().insertContentAt(posAfter, [
                          { type: 'image', attrs: { src, alt } },
                        ]).run();
                        
                      } catch (error) {
                        console.error('Image upload failed:', error);
                      }
                    };
                    input.click();
                  } catch {}
                }}
              >
                Upload Image
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


