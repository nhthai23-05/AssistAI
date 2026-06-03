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

  useEffect(() => {
    try { localStorage.setItem("assistai_module", active); } catch {}
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

  let moduleEl = null;
  if (active === "chat")     moduleEl = <ChatModule userId={userId} userEmail={userEmail}/>;
  if (active === "calendar") moduleEl = <CalendarModule userId={userId}/>;
  if (active === "sheets")   moduleEl = <SheetsModule userId={userId}/>;
  if (active === "settings") moduleEl = <SettingsModule onLogout={handleLogout} userEmail={userEmail}/>;

  return (
    <div className="app">
      <IconRail active={active} onChange={setActive} onLogout={handleLogout}/>
      {moduleEl}
    </div>
  );
}
