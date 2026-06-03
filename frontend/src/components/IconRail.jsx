import React from 'react';
import I from './icons';

export function IconRail({ active, onChange, onLogout, unread }) {
  const items = [
    { id: "chat",     label: "Trò chuyện", icon: <I.Chat/>,    badge: unread },
    { id: "calendar", label: "Lịch",       icon: <I.CalGrid/> },
    { id: "sheets",   label: "Thu chi",    icon: <I.Sheet/> },
  ];
  return (
    <nav className="rail">
      <div className="rail-logo" aria-hidden>
        <I.Logo style={{ width: 20, height: 20, stroke: "#fff" }}/>
      </div>
      {items.map(it => (
        <button key={it.id} className={"rail-btn" + (active === it.id ? " active" : "")} onClick={() => onChange(it.id)}>
          {it.icon}
          {it.badge ? <span className="badge">{it.badge}</span> : null}
          <span className="rail-tooltip">{it.label}</span>
        </button>
      ))}
      <div className="rail-spacer"/>
      <button className={"rail-btn" + (active === "settings" ? " active" : "")} onClick={() => onChange("settings")}>
        <I.Settings/>
        <span className="rail-tooltip">Cài đặt</span>
      </button>
      <button className="rail-btn" onClick={onLogout}>
        <I.Logout/>
        <span className="rail-tooltip">Đăng xuất</span>
      </button>
      <div style={{ height: 4 }}/>
      <div className="avatar" style={{ width: 32, height: 32, fontSize: 11.5 }}>KH</div>
    </nav>
  );
}
