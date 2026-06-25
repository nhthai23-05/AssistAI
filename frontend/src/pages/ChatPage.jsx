import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { Thread } from '../components/Thread';
import { Welcome } from '../components/Welcome';
import { Composer } from '../components/Composer';
import { MODELS } from '../data/models';
import API from '../services/api';

function getIntentLabel(actions) {
  if (!actions || actions.length === 0) return "Trò chuyện";
  const types = actions.map(a => a.type);
  if (types.some(t => t === "write_income_sheet")) return "Thu nhập";
  if (types.some(t => t === "write_sheet")) return "Chi tiêu";
  if (types.some(t => t === "create_event")) return "Tạo lịch";
  if (types.some(t => t === "update_event")) return "Cập nhật lịch";
  if (types.some(t => t === "delete_event")) return "Xóa lịch";
  return "Trò chuyện";
}

export function ChatModule({ userId, userEmail }) {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [model, setModel] = useState("assist-pro");
  const [draft, setDraft] = useState("");
  const [imageBase64, setImageBase64] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [loading, setLoading] = useState(true);
  const loadedSessions = useRef(new Set());

  // Load sessions from backend on mount
  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    API.listSessions(userId)
      .then(sessions => {
        const convs = sessions.map(s => ({
          id: "sess-" + s.session_id,
          sessionId: s.session_id,
          title: s.title || "Cuộc trò chuyện",
          updatedAt: new Date(s.last_message_at).getTime(),
          pinned: false,
          model: "assist-pro",
          messages: [],
          messagesLoaded: false,
        }));
        setConversations(convs);
        if (convs.length > 0) setActiveId(convs[0].id);
      })
      .catch(err => console.error("Failed to load sessions:", err))
      .finally(() => setLoading(false));
  }, [userId]);

  // Lazy-load messages when switching to a conversation
  useEffect(() => {
    const conv = conversations.find(c => c.id === activeId);
    if (!conv?.sessionId || !userId || loadedSessions.current.has(conv.sessionId)) return;
    loadedSessions.current.add(conv.sessionId);

    API.getChatHistory(userId, conv.sessionId, 50)
      .then(data => {
        const msgs = (data.messages || []).map(m => ({
          role: m.role === "assistant" ? "ai" : "user",
          text: m.content,
          messageId: m.message_id,
          ...(m.actions?.length ? {
            actions: m.actions.map(a => ({ type: a.action_type, status: a.action_status, data: a.data || {} }))
          } : {}),
        }));
        setConversations(prev =>
          prev.map(c => c.sessionId === conv.sessionId
            ? { ...c, messages: msgs, messagesLoaded: true }
            : c
          )
        );
      })
      .catch(err => {
        loadedSessions.current.delete(conv.sessionId);
        console.error("Failed to load history:", err);
      });
  }, [activeId, userId]);

  const active = useMemo(
    () => conversations.find(c => c.id === activeId),
    [conversations, activeId]
  );

  const isEmpty = !active || active.messages.length === 0;

  const updateActive = (mutator) => {
    setConversations(prev =>
      prev.map(c => c.id === activeId ? mutator(c) : c)
    );
  };

  const handleNew = useCallback(() => {
    const newConv = {
      id: "c-" + Math.random().toString(36).slice(2, 9),
      sessionId: null,
      title: "Cuộc trò chuyện mới",
      updatedAt: Date.now(),
      pinned: false,
      model,
      messages: [],
      messagesLoaded: true,
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveId(newConv.id);
    setDraft("");
  }, [model]);

  const handleDelete = (id) => {
    const conv = conversations.find(c => c.id === id);
    if (conv?.sessionId) {
      API.deleteSession(userId, conv.sessionId).catch(console.error);
    }
    setConversations(prev => {
      const next = prev.filter(c => c.id !== id);
      if (id === activeId) setActiveId(next.length > 0 ? next[0].id : null);
      return next;
    });
  };

  const handleSelect = (id) => {
    setActiveId(id);
    setDraft("");
  };

  const handleModelChange = (m) => {
    setModel(m);
    updateActive(c => ({ ...c, model: m }));
  };

  const handleSend = async (textOverride) => {
    const text = (textOverride ?? draft).trim();
    const img = imageBase64;
    if ((!text && !img) || isTyping) return;

    let currentConv = conversations.find(c => c.id === activeId);
    let convId = activeId;

    // Auto-create a conversation if none is active
    if (!currentConv) {
      convId = "c-" + Math.random().toString(36).slice(2, 9);
      currentConv = {
        id: convId,
        sessionId: null,
        title: "Cuộc trò chuyện",
        updatedAt: Date.now(),
        pinned: false,
        model,
        messages: [],
        messagesLoaded: true,
      };
      setConversations(prev => [currentConv, ...prev]);
      setActiveId(convId);
    }

    const update = (mutator) => setConversations(prev => prev.map(c => c.id === convId ? mutator(c) : c));

    update(c => ({
      ...c,
      messages: [...c.messages, { role: "user", text, ...(img ? { image: img } : {}) }],
      updatedAt: Date.now(),
    }));

    setDraft("");
    setImageBase64(null);
    setIsTyping(true);

    // Strip data-URL prefix before sending to backend
    const imgPayload = img ? img.split(",")[1] : null;

    try {
      const resp = await API.sendMessage(userId, text, currentConv?.sessionId || null, imgPayload);

      // Persist session_id returned by the first message
      if (!currentConv?.sessionId && resp.session_id) {
        loadedSessions.current.add(resp.session_id);
        setConversations(prev =>
          prev.map(c => c.id === convId
            ? { ...c, sessionId: resp.session_id, messagesLoaded: true }
            : c
          )
        );
      }

      const actions = (resp.actions || []).map(a => ({
        type: a.action_type,
        status: a.action_status,
        data: a.data || {},
      }));

      update(c => {
        const aiMsg = { role: "ai", text: resp.response, ...(actions.length > 0 ? { actions } : {}), ...(resp.tokens_used ? { tokens: resp.tokens_used } : {}) };
        const isFirstReply = c.messages.length === 1;
        let nextTitle = c.title;
        if (isFirstReply) {
          if (resp.suggested_title) {
            nextTitle = resp.suggested_title;
          } else {
            const d = new Date();
            const dateStr = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
            nextTitle = `${dateStr} · ${getIntentLabel(actions)}`;
          }
        }
        return { ...c, title: nextTitle, messages: [...c.messages, { ...aiMsg, messageId: resp.message_id }], updatedAt: Date.now() };
      });
    } catch (err) {
      update(c => ({
        ...c,
        messages: [...c.messages, { role: "ai", text: `❌ Lỗi kết nối: ${err.message}` }],
      }));
    } finally {
      setIsTyping(false);
    }
  };

  const handleStop = () => {};

  const handleActionAccept = async (msgIdx, actionIdx) => {
    const conv = conversations.find(c => c.id === activeId);
    const msg = conv?.messages[msgIdx];
    const action = msg?.actions?.[actionIdx];
    if (!action) return;

    const messageId = msg.messageId;

    updateActive(c => ({
      ...c,
      messages: c.messages.map((m, i) => {
        if (i !== msgIdx) return m;
        return { ...m, actions: m.actions.map((a, ai) => ai === actionIdx ? { ...a, status: "accepted" } : a) };
      }),
    }));

    try {
      if (action.type === "create_event") {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        await API.createEvent(userId, { ...action.data, timezone: tz });
      } else if (action.type === "write_sheet") {
        const items = Array.isArray(action.data) ? action.data : [action.data];
        for (const item of items) {
          await API.addExpense(userId, item);
        }
      } else if (action.type === "write_income_sheet") {
        const items = Array.isArray(action.data) ? action.data : [action.data];
        for (const item of items) {
          await API.addIncome(userId, item);
        }
      } else if (action.type === "update_event") {
        const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const { event_id, event_summary, ...updates } = action.data;
        await API.updateEvent(userId, event_id, { ...updates, timezone: tz });
      } else if (action.type === "delete_event") {
        await API.deleteEvent(userId, action.data.event_id);
      }
      if (messageId) API.updateActionStatus(userId, messageId, actionIdx, "accepted").catch(err => console.error("Failed to persist action status:", err));
    } catch (err) {
      // Roll back and show error
      updateActive(c => ({
        ...c,
        messages: [
          ...c.messages.map((m, i) => {
            if (i !== msgIdx) return m;
            return { ...m, actions: m.actions.map((a, ai) => ai === actionIdx ? { ...a, status: "pending" } : a) };
          }),
          { role: "ai", text: `❌ Không thực hiện được: ${err.message}` },
        ],
      }));
    }
  };

  const handleActionReject = (msgIdx, actionIdx) => {
    const conv = conversations.find(c => c.id === activeId);
    const messageId = conv?.messages[msgIdx]?.messageId;

    updateActive(c => {
      const msgs = c.messages.map((m, i) => {
        if (i !== msgIdx) return m;
        const actions = m.actions.map((a, ai) =>
          ai === actionIdx ? { ...a, status: "rejected" } : a
        );
        return { ...m, actions };
      });
      return { ...c, messages: msgs };
    });

    if (messageId) API.updateActionStatus(userId, messageId, actionIdx, "rejected").catch(err => console.error("Failed to persist action status:", err));
  };

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "n") {
        e.preventDefault();
        handleNew();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleNew]);

  const modelObj = MODELS.find(m => m.id === (active?.model || model)) || MODELS[0];

  if (loading) {
    return (
      <>
        <aside className="sidebar">
          <div className="sb-head">
            <div className="brand">
              <div className="brand-mark">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round">
                  <path d="m12 3 4 5-4 13-4-13 4-5Z" fill="rgba(255,255,255,.18)"/>
                </svg>
              </div>
              <div className="brand-name"><b>AssistAI</b></div>
            </div>
          </div>
        </aside>
        <main className="module-main" style={{ alignItems:"center", justifyContent:"center", display:"flex" }}>
          <div style={{ color:"var(--text-3)", fontSize:14 }}>Đang tải…</div>
        </main>
      </>
    );
  }

  return (
    <>
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelect}
        onNew={handleNew}
        onDelete={handleDelete}
        userEmail={userEmail}
      />
      <main className="module-main">
        <TopBar
          title={active?.title || "Cuộc trò chuyện mới"}
          model={active?.model || model}
          models={MODELS}
          onModelChange={handleModelChange}
        />
        {isEmpty ? (
          <Welcome onPick={(t) => handleSend(t)} />
        ) : (
          <Thread
            messages={active.messages}
            isTyping={isTyping}
            onActionAccept={handleActionAccept}
            onActionReject={handleActionReject}
          />
        )}
        <Composer
          value={draft}
          onChange={setDraft}
          onSend={() => handleSend()}
          onStop={handleStop}
          isTyping={isTyping}
          modelLabel={modelObj.name}
          image={imageBase64}
          onImageChange={setImageBase64}
        />
      </main>
    </>
  );
}
