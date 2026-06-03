import React, { useState, useMemo } from 'react';
import I from './icons';

export function Sidebar({ conversations, activeId, onSelect, onNew, onDelete, userEmail }) {
  const displayName = userEmail ? userEmail.split("@")[0] : "User";
  const initials = displayName.slice(0, 2).toUpperCase();
  const [query, setQuery] = useState("");

  const groups = useMemo(() => {
    const now = new Date();
    const startOfDay = new Date(now); startOfDay.setHours(0,0,0,0);
    const dayMs = 86400000;
    const buckets = { "Đã ghim": [], "Hôm nay": [], "Hôm qua": [], "7 ngày trước": [], "Cũ hơn": [] };
    const q = query.trim().toLowerCase();
    const filtered = q ? conversations.filter(c => c.title.toLowerCase().includes(q)) : conversations;
    for (const c of filtered) {
      if (c.pinned) { buckets["Đã ghim"].push(c); continue; }
      const ageDays = (startOfDay.getTime() - new Date(c.updatedAt).setHours(0,0,0,0)) / dayMs;
      if (ageDays <= 0) buckets["Hôm nay"].push(c);
      else if (ageDays === 1) buckets["Hôm qua"].push(c);
      else if (ageDays <= 7) buckets["7 ngày trước"].push(c);
      else buckets["Cũ hơn"].push(c);
    }
    return Object.entries(buckets)
      .filter(([_, arr]) => arr.length > 0)
      .map(([label, arr]) => ({ label, items: arr.sort((a,b) => b.updatedAt - a.updatedAt) }));
  }, [conversations, query]);

  return (
    <aside className="sidebar">
      <div className="sb-head">
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round">
              <path d="m12 3 4 5-4 13-4-13 4-5Z" fill="rgba(255,255,255,.18)"/>
            </svg>
          </div>
          <div className="brand-name"><b>AssistAI</b></div>
        </div>
        <button className="icon-btn" title="Collapse sidebar"><I.Panel/></button>
      </div>
      <button className="new-chat" onClick={onNew}>
        <span className="plus"><I.Plus/></span>
        Cuộc trò chuyện mới
        <span className="kbd">⌘N</span>
      </button>
      <div className="search-wrap">
        <I.Search style={{ color: "var(--text-3)" }}/>
        <input placeholder="Tìm cuộc trò chuyện" value={query} onChange={(e) => setQuery(e.target.value)}/>
      </div>
      <div className="sb-list">
        {groups.length === 0 && (
          <div style={{ padding: "20px 12px", fontSize: 13, color: "var(--text-3)" }}>
            Không tìm thấy cuộc trò chuyện nào khớp với "{query}".
          </div>
        )}
        {groups.map(group => (
          <div key={group.label}>
            <div className="sb-group-label">{group.label}</div>
            {group.items.map(c => (
              <div key={c.id} className={"conv" + (c.id === activeId ? " active" : "")} onClick={() => onSelect(c.id)}>
                {c.pinned && group.label === "Đã ghim" && <span className="conv-pin" aria-label="đã ghim"><I.Pin/></span>}
                <span className="conv-title">{c.title}</span>
                <button className="conv-more" title="Xóa cuộc trò chuyện" onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}>
                  <I.Trash/>
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>
      <div className="sb-foot">
        <div className="user-card">
          <div className="avatar">{initials}</div>
          <div className="user-info">
            <div className="name">{displayName}</div>
            <div className="plan"><span className="plan-dot"/> {userEmail || ""}</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
