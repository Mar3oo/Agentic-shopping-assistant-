import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, User } from 'lucide-react';
import type { ChatMessage } from '../store/AppContext';
import RECOAvatar, { type AvatarState } from './RECOAvatar';

interface Props {
  messages: ChatMessage[];
  onSend: (msg: string) => void;
  placeholder?: string;
  loading?: boolean;
  emptyText?: string;
  disabled?: boolean;
}

const msgAnim = {
  initial: { opacity: 0, y: 8, scale: 0.97 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit:    { opacity: 0, scale: 0.95 },
};

export default function ChatBox({ messages, onSend, placeholder = 'Type a message…', loading = false, emptyText, disabled = false }: Props) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const isRTL = document.documentElement.dir === 'rtl' || document.body.dir === 'rtl';

  const defaultEmpty = isRTL ? 'لا توجد محادثة بعد.' : 'No conversation yet.';
  const defaultHint  = isRTL ? 'اسألني عن أي منتج، سعر أو مقارنة.' : 'Ask me about any product, price or comparison.';

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = () => {
    const t = input.trim();
    if (!t || disabled || loading) return;
    onSend(t);
    setInput('');
  };

  // Derive avatar state from context
  const avatarState: AvatarState = loading ? 'thinking' : input.length > 0 ? 'listening' : 'idle';

  return (
    <div className="chat-box-layout">
      {/* Avatar column — always visible beside chat */}
      <div className="chat-avatar-col">
        <RECOAvatar
          size={96}
          avatarState={avatarState}
          interactive
          showThoughts={loading}
        />
      </div>

      {/* Messages + input */}
      <div className="chat-box">
        <div className="chat-messages">

          {/* Empty state */}
          {messages.length === 0 && !loading && (
            <motion.div
              className="chat-empty-avatar-state"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              <RECOAvatar size={110} avatarState="idle" interactive showThoughts={false} />
              <div className="chat-empty-avatar-label">{emptyText || defaultEmpty}</div>
              <div className="chat-empty-avatar-hint">{defaultHint}</div>
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                className={`chat-msg ${msg.role === 'user' ? 'user-msg' : ''}`}
                {...msgAnim}
                transition={{ duration: 0.22 }}
              >
                <div
                  className={`chat-av ${msg.role === 'assistant' ? 'bot' : 'usr'}`}
                  style={msg.role === 'assistant' ? { background: 'transparent', border: 'none', padding: 0, overflow: 'visible', width: 32, height: 32 } : {}}
                >
                  {msg.role === 'assistant'
                    ? <RECOAvatar size={32} avatarState="idle" interactive={false} />
                    : <User size={13} />}
                </div>
                <div className={`chat-bubble ${msg.role === 'assistant' ? 'bot-msg' : 'usr-msg'}`}>
                  <p>{msg.content}</p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div className="chat-msg" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <div className="chat-av bot" style={{ background: 'transparent', border: 'none', padding: 0, overflow: 'visible', width: 32, height: 32 }}>
                <RECOAvatar size={32} avatarState="thinking" interactive={false} />
              </div>
              <div className="chat-bubble bot-msg typing">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </motion.div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="chat-input-bar">
          <button className="chat-attach-btn" title={isRTL ? 'إرفاق ملف' : 'Attach file'}>
            <Paperclip size={15} />
          </button>
          <input
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={disabled ? (isRTL ? 'ابدأ جلسة أولاً.' : 'Start a session first.') : placeholder}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            disabled={disabled || loading}
          />
          <motion.button
            className="chat-send"
            onClick={send}
            disabled={!input.trim() || disabled || loading}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
          >
            {loading ? <span className="spinner" /> : <Send size={14} />}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
