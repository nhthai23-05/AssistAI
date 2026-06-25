import React, { useState, useEffect } from 'react';
import { IconRail } from './components/IconRail';
import { ChatModule } from './pages/ChatPage';
import { CalendarModule } from './pages/CalendarPage';
import { SheetsModule } from './pages/SheetsPage';
import { SettingsModule } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';

export default function App() {
  const [authed, setAuthed] = useState(() => {
    try { return localStorage.getItem("assistai_authed") === "1"; } catch { return false; }
  });
  const [userId, setUserId] = useState(() => {
    try { const id = localStorage.getItem("assistai_user_id"); return id ? parseInt(id, 10) : null; } catch { return null; }
  });
  const [userEmail, setUserEmail] = useState(() => {
    try { return localStorage.getItem("assistai_email") || ""; } catch { return ""; }
  });
  const [active, setActive] = useState(() => {
    try { return localStorage.getItem("assistai_module") || "chat"; } catch { return "chat"; }
  });
  // Tracks which tabs have been visited so they stay mounted (hidden via CSS) instead of unmounting.
  const [visited, setVisited] = useState(() => {
    try { return new Set([localStorage.getItem("assistai_module") || "chat"]); } catch { return new Set(["chat"]); }
  });

  useEffect(() => {
    try { localStorage.setItem("assistai_module", active); } catch {}
    setVisited(prev => {
      if (prev.has(active)) return prev;
      const next = new Set(prev);
      next.add(active);
      return next;
    });
  }, [active]);

  const handleLogin = (uid, email) => {
    setAuthed(true);
    setUserId(uid);
    setUserEmail(email || "");
    try {
      localStorage.setItem("assistai_authed", "1");
      localStorage.setItem("assistai_user_id", String(uid));
      if (email) localStorage.setItem("assistai_email", email);
    } catch {}
  };

  const handleLogout = async () => {
    setAuthed(false);
    setUserId(null);
    setUserEmail("");
    try {
      localStorage.removeItem("assistai_authed");
      localStorage.removeItem("assistai_user_id");
      localStorage.removeItem("assistai_email");
    } catch {}
  };

  if (!authed) return <LoginPage onLogin={handleLogin}/>;

  const show = (tab) => active !== tab ? { display: "none" } : { display: "contents" };

  return (
    <div className="app">
      <IconRail active={active} onChange={setActive} onLogout={handleLogout}/>
      {visited.has("chat")     && <div style={show("chat")}><ChatModule userId={userId} userEmail={userEmail}/></div>}
      {visited.has("calendar") && <div style={show("calendar")}><CalendarModule userId={userId}/></div>}
      {visited.has("sheets")   && <div style={show("sheets")}><SheetsModule userId={userId}/></div>}
      {visited.has("settings") && <div style={show("settings")}><SettingsModule onLogout={handleLogout} userEmail={userEmail}/></div>}
    </div>
  );
}
