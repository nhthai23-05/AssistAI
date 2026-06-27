import React, { useState, useEffect, useRef } from 'react';
import I from './icons';

function ModelSelector({ models, value, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const current = models.find(m => m.id === value) || models[0];

  const iconFor = (kind) => {
    switch (kind) {
      case "diamond": return <I.Diamond/>;
      case "lightning": return <I.Lightning/>;
      case "brain": return <I.Brain/>;
      default: return <I.Sparkle/>;
    }
  };

  return (
    <div className="model-select" ref={ref}>
      <button className="model-trigger" onClick={() => setOpen(o => !o)}>
        <span className="model-dot">{iconFor(current.icon)}</span>
        <span className="model-name"><b>{current.name.replace(/^AssistAI /, "")}</b><span> · {current.tag || "Standard"}</span></span>
        <I.Chev style={{ color: "var(--text-2)" }}/>
      </button>
      {open && (
        <div className="model-menu" role="menu">
          {models.map(m => (
            <div key={m.id} className="model-opt" role="menuitem" onClick={() => { onChange(m.id); setOpen(false); }}>
              <span className={"mo-icon" + (m.brand ? " brand" : "")}>{iconFor(m.icon)}</span>
              <div>
                <div className="mo-title">{m.name}{m.tag && <span className="mo-badge">{m.tag}</span>}</div>
                <div className="mo-desc">{m.desc}</div>
              </div>
              {m.id === value && <span className="mo-check"><I.Check/></span>}
            </div>
          ))}
          <div className="menu-sep"/>
          <div className="model-opt" style={{ gridTemplateColumns: "28px 1fr" }}>
            <span className="mo-icon"><I.Settings/></span>
            <div>
              <div className="mo-title">Cài đặt mô hình</div>
              <div className="mo-desc">Nhiệt độ, system prompt, tools</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function TopBar({ title }) {
  return (
    <header className="topbar">
      <div className="title"><span className="title-text">{title}</span></div>
      <div className="tb-actions">
        <button className="icon-btn" title="Thêm"><I.More/></button>
      </div>
    </header>
  );
}
