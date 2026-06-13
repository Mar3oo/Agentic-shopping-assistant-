import { useRef, useEffect, useState, ReactNode } from 'react';
import { useApp } from '../store/AppContext';
import { useT } from '../i18n/translations';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, ArrowDownCircle, Sparkles } from 'lucide-react';
import type { ChatMessage } from '../store/AppContext';

interface Props {
  messages: ChatMessage[];
  onSend: (msg: string) => void;
  placeholder?: string;
  loading?: boolean;
  emptyText?: string;
  disabled?: boolean;
  renderPayload?: (payload: any) => ReactNode;
}

const msgAnim = {
  initial: { opacity: 0, y: 12, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit:    { opacity: 0, scale: 0.98 },
};

export default function ChatBox({ messages, onSend, placeholder, loading = false, emptyText, disabled = false, renderPayload }: Props) {
  const { state } = useApp();
  const t = useT(state.lang);
  const [input, setInput] = useState('');
  const [showScrollDown, setShowScrollDown] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasMounted = useRef(false);
  const isRTL = state.lang === 'ar';

  const isAtBottom = (el: HTMLDivElement) => {
    return el.scrollHeight - el.scrollTop - el.clientHeight < 100;
  };

  const handleMessagesScroll = () => {
    const el = messagesRef.current;
    if (!el) return;
    setShowScrollDown(!isAtBottom(el));
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

  const send = () => {
    const t = input.trim();
    if (!t || disabled || loading) return;
    onSend(t);
    setInput('');
  };

  return (
    <div className="chat-box-conversational">
      <div className="chat-messages-flow" ref={messagesRef} onScroll={handleMessagesScroll}>
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-row ${msg.role === 'user' ? 'user-row' : 'bot-row'}`}>
              <motion.div
                className={`chat-msg-v2 ${msg.role === 'user' ? 'user-msg' : 'bot-msg'}`}
                {...msgAnim}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              >
                <div className="msg-header">
                  <div className={`msg-icon ${msg.role === 'assistant' ? 'bot' : 'usr'}`}>
                    {msg.role === 'assistant' ? <Sparkles size={12} /> : <User size={12} />}
                  </div>
                  <span className="msg-role-name">
                    {msg.role === 'assistant' ? 'RECO' : t('yourName')}
                  </span>
                </div>
                
                <div className="msg-content">
                  {msg.content && <p className="text-content">{msg.content}</p>}
                  
                  {msg.payload && renderPayload && (
                    <div className="payload-content">
                      {renderPayload(msg.payload)}
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          ))}
        </AnimatePresence>

        {loading && (
          <div className="chat-row bot-row">
            <motion.div className="chat-msg-v2 bot-msg typing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="msg-header">
                <div className="msg-icon bot"><Sparkles size={12} /></div>
                <span className="msg-role-name">RECO</span>
              </div>
              <div className="typing-dots">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </motion.div>
          </div>
        )}
        
        <div ref={bottomRef} className="chat-bottom-anchor" />
      </div>

      {showScrollDown && (
        <button
          type="button"
          className="chat-scroll-btn"
          onClick={() => {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
            setShowScrollDown(false);
          }}
        >
          <ArrowDownCircle size={18} />
        </button>
      )}

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-textarea"
            rows={1}
            value={input}
            onChange={e => {
              setInput(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            placeholder={placeholder || t('askRefinements')}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
                (e.target as HTMLTextAreaElement).style.height = 'auto';
              }
            }}
            disabled={disabled || loading}
          />
          <button
            className="chat-send-v2"
            onClick={send}
            disabled={!input.trim() || disabled || loading}
          >
            {loading ? <div className="loading-spinner-sm" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}

