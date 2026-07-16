export function TypingIndicator() {
  return (
    <>
      <style>{`
        .typing-indicator-container {
          background: var(--color-bg-elevated);
          border: 1px solid var(--color-border-default);
          padding: 12px 16px;
          border-radius: 16px 16px 16px 0;
          width: fit-content;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .typing-dot {
          width: 6px;
          height: 6px;
          background: var(--color-text-secondary);
          border-radius: 50%;
          animation: typing-bounce 1.4s infinite ease-in-out both;
        }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes typing-bounce {
          0%, 80%, 100% { transform: scale(0.3); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
      <div className="typing-indicator-container">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </>
  )
}
