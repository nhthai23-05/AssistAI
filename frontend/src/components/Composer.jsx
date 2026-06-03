import React, { useRef, useEffect } from 'react';
import I from './icons';

export function Composer({ value, onChange, onSend, onStop, isTyping, modelLabel }) {
  const taRef = useRef(null);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isTyping && value.trim()) onSend();
    }
  };

  const canSend = value.trim().length > 0 && !isTyping;

  return (
    <div className="composer-wrap">
      <div className="composer">
        <div className="composer-inner">
          <textarea
            ref={taRef}
            value={value}
            onChange={e => onChange(e.target.value)}
            onKeyDown={onKey}
            placeholder="Hỏi AssistAI bất cứ điều gì…  (Shift+Enter để xuống dòng)"
            rows={1}
          />
          <div className="composer-toolbar">
            <button className="cmp-btn" title="Đính kèm file"><I.Paperclip/></button>
            <button className="cmp-btn" title="Đính kèm ảnh"><I.Image/></button>
            <button className="cmp-btn" title="Tìm trên web"><I.Globe/> <span>Search</span></button>
            <button className="cmp-btn" title="Nhập bằng giọng nói"><I.Mic/></button>
            <span className="cmp-spacer"/>
            <span style={{ fontSize: 11.5, color: "var(--text-3)", marginRight: 6 }}>{modelLabel}</span>
            {isTyping ? (
              <button className="send-btn stopping" onClick={onStop} title="Dừng"><I.Stop/></button>
            ) : (
              <button
                className={"send-btn" + (canSend ? " active" : "")}
                onClick={() => canSend && onSend()}
                disabled={!canSend}
                title="Gửi"
              >
                <I.Send/>
              </button>
            )}
          </div>
        </div>
      </div>
      <div className="composer-foot">
        AssistAI có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng. Nhấn <kbd>↵</kbd> để gửi, <kbd>⇧</kbd>+<kbd>↵</kbd> để xuống dòng.
      </div>
    </div>
  );
}
