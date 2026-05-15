import { useRef, useEffect, useState } from 'react';
import { useApp } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, User, ArrowDownCircle } from 'lucide-react';
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

export default function ChatBox({ messages, onSend, placeholder, loading = false, emptyText, disabled = false }: Props) {
  const { state } = useApp();
  const t = useT(state.lang);
  const [input, setInput] = useState('');
  const [showScrollDown, setShowScrollDown] = useState(false);
  const [showScrollToChat, setShowScrollToChat] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const chatRootRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasMounted = useRef(false);
  const isRTL = state.lang === 'ar';

  const defaultEmpty = emptyText ?? t('noConversation');
  const defaultHint = t('askRefinements');

  const isAtBottom = (el: HTMLDivElement) => {
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  const handleMessagesScroll = () => {
    const el = messagesRef.current;
    if (!el) return;
    setShowScrollDown(!isAtBottom(el));
  };

  const handleWindowScroll = () => {
    const el = chatRootRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setShowScrollToChat(rect.top > window.innerHeight - 120 || rect.bottom < 140);
  };

  useEffect(() => {
    const el = messagesRef.current;
    if (!hasMounted.current) {
      hasMounted.current = true;
      if (el) setShowScrollDown(!isAtBottom(el));
      return;
    }

    if (el && isAtBottom(el)) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      setShowScrollDown(false);
    } else if (el) {
      setShowScrollDown(true);
    }
  }, [messages.length, loading]);

  useEffect(() => {
    handleWindowScroll();
    window.addEventListener('scroll', handleWindowScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleWindowScroll);
  }, []);

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
      <div className="chat-box" ref={chatRootRef}>
        <div className="chat-messages" ref={messagesRef} onScroll={handleMessagesScroll}>

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

          {showScrollDown && (
            <button
              type="button"
              className="chat-scroll-down"
              onClick={() => {
                bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
                setShowScrollDown(false);
              }}
              title={isRTL ? 'انتقل إلى آخر المحادثة' : 'Jump to latest chat'}
            >
              <ArrowDownCircle size={20} />
            </button>
          )}

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

        {showScrollToChat && (
          <button
            type="button"
            className="scroll-to-chat-button"
            onClick={() => chatRootRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            title={isRTL ? 'العودة إلى المحادثة' : 'Back to chat'}
          >
            <ArrowDownCircle size={20} />
          </button>
        )}

        {/* Input bar */}
          <div className="chat-input-bar">
          <button className="chat-attach-btn" title={isRTL ? 'إرفاق ملف' : 'Attach file'}>
            <Paperclip size={15} />
          </button>
          <input
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={disabled ? t('startSession') : (placeholder || t('askRefinements'))}
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
