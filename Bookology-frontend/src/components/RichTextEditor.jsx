import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import TextAlign from '@tiptap/extension-text-align';
import CharacterCount from '@tiptap/extension-character-count';

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

  return <EditorContent editor={editor} className={className} />;
}


