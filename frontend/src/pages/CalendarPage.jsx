import React, { useState, useMemo, useRef, useEffect } from 'react';
import I from '../components/icons';
import API from '../services/api';
import { fmtTimeVN } from '../data/expenses';

const _dowLabels = ["T2","T3","T4","T5","T6","T7","CN"];
const _monthLabels = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6","Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"];

function startOfWeek(d) {
  const x = new Date(d);
  const dow = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - dow);
  x.setHours(0,0,0,0);
  return x;
}
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate()+n); return x; };
const addMonths = (d, n) => { const x = new Date(d); x.setMonth(x.getMonth()+n); return x; };
const sameDay = (a, b) => new Date(a).toDateString() === new Date(b).toDateString();

function MiniCalendar({ selected, onSelect, events }) {
  const [view, setView] = useState(() => { const d = new Date(selected); d.setDate(1); return d; });

  const year = view.getFullYear();
  const month = view.getMonth();
  const first = new Date(year, month, 1);
  const lead = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month+1, 0).getDate();

  const cells = [];
  for (let i=0; i<lead; i++) cells.push({ muted:true, n: new Date(year, month, -lead+i+1).getDate(), d: new Date(year, month, -lead+i+1)});
  for (let i=1; i<=daysInMonth; i++) cells.push({ n: i, d: new Date(year, month, i) });
  while (cells.length % 7 !== 0) cells.push({ muted:true, n: cells.length - lead - daysInMonth + 1, d: new Date(year, month+1, cells.length - lead - daysInMonth + 1)});

  const eventDays = new Set(events.map(e => new Date(e.start).toDateString()));
  const today = new Date();

  return (
    <div className="minical">
      <div className="minical-head">
        <button onClick={() => setView(new Date(year, month-1, 1))}><I.ChevLeft/></button>
        <div className="mc-month">{_monthLabels[month]} {year}</div>
        <button onClick={() => setView(new Date(year, month+1, 1))} style={{ transform:"rotate(180deg)"}}><I.ChevLeft/></button>
      </div>
      <div className="minical-grid">
        {_dowLabels.map(d => <div key={d} className="mc-dow">{d}</div>)}
        {cells.map((c, i) => {
          const isToday = sameDay(c.d, today);
          const isSelected = sameDay(c.d, selected);
          const hasEv = eventDays.has(c.d.toDateString());
          let cls = "mc-day";
          if (c.muted) cls += " muted";
          if (isToday && !isSelected) cls += " today";
          if (isSelected) cls += " selected";
          if (hasEv && !c.muted) cls += " has-event";
          return (
            <div key={i} className={cls} onClick={() => onSelect(c.d)}>{c.n}</div>
          );
        })}
      </div>
    </div>
  );
}

function UpcomingList({ events, onSelect }) {
  const upcoming = useMemo(() => {
    const now = Date.now();
    return events
      .filter(e => e.end > now)
      .sort((a,b) => a.start - b.start)
      .slice(0, 5);
  }, [events]);

  return (
    <div className="sb-section">
      <div className="sb-section-title row">
        <span>Sắp diễn ra</span>
        <span style={{ fontSize: 11, color: "var(--text-3)"}}>{upcoming.length}</span>
      </div>
      {upcoming.length === 0 && (
        <div style={{ padding: "12px 4px", fontSize: 12.5, color: "var(--text-3)"}}>
          Không có sự kiện nào sắp tới.
        </div>
      )}
      {upcoming.map(e => {
        const d = new Date(e.start);
        const isToday = sameDay(d, new Date());
        const isTomorrow = sameDay(d, addDays(new Date(), 1));
        const dayLabel = isToday ? "Hôm nay" : isTomorrow ? "Ngày mai" : d.toLocaleDateString("vi-VN", { weekday: "short", day:"2-digit", month:"2-digit"});
        return (
          <div key={e.id} className="upcoming-item" onClick={() => onSelect(e)}>
            <div className={"u-bar " + (e.color === "violet" ? "" : e.color)}/>
            <div className="u-body">
              <div className="u-title">{e.summary}</div>
              <div className="u-meta">
                <I.Clock style={{ width: 11, height: 11 }}/>
                {dayLabel} · {fmtTimeVN(e.start)}–{fmtTimeVN(e.end)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CalendarSidebar({ selected, onSelect, events, onCreate }) {
  return (
    <aside className="sidebar">
      <div className="sb-head">
        <div className="brand">
          <div className="brand-mark"><I.CalGrid style={{ width:14, height:14, stroke:"#fff", strokeWidth:2.2, fill:"none" }}/></div>
          <div className="brand-name"><b>Lịch</b></div>
        </div>
      </div>

      <button className="new-chat" onClick={onCreate} style={{ marginBottom: 14 }}>
        <span className="plus"><I.Plus/></span>
        Tạo sự kiện
        <span className="kbd">⌘E</span>
      </button>

      <MiniCalendar selected={selected} onSelect={onSelect} events={events}/>

      <div className="sb-list">
        <UpcomingList events={events} onSelect={() => {}}/>
      </div>

      <div className="sb-foot">
        <div style={{ display:"flex", alignItems:"center", gap: 8, fontSize:12, color:"var(--text-2)", padding:"4px 6px"}}>
          <span className="plan-dot" style={{ background:"var(--success)"}}/>
          Đã đồng bộ với Google Calendar
        </div>
      </div>
    </aside>
  );
}

function layoutDayEvents(dayEvents) {
  const evs = [...dayEvents].sort((a,b) => a.start - b.start);
  const cols = [];
  evs.forEach(ev => {
    let placed = false;
    for (let i=0; i<cols.length; i++) {
      const col = cols[i];
      const last = col[col.length-1];
      if (last.end <= ev.start) {
        col.push(ev);
        ev._col = i;
        placed = true;
        break;
      }
    }
    if (!placed) {
      cols.push([ev]);
      ev._col = cols.length - 1;
    }
  });
  const totalCols = cols.length;
  evs.forEach(ev => { ev._cols = totalCols; });
  return evs;
}

function TimeGrid({ colDays, events, onSelectEvent }) {
  const today = new Date();
  const hours = Array.from({length: 17}, (_,i) => i + 6);
  const hourHeight = 48;
  const HOUR_START = 6;

  const dayEventMap = useMemo(() => {
    const map = colDays.map(() => []);
    events.forEach(e => {
      const idx = colDays.findIndex(d => sameDay(d, new Date(e.start)));
      if (idx >= 0) map[idx].push(e);
    });
    return map.map(layoutDayEvents);
  }, [events, colDays]);

  const nowMin = today.getHours() * 60 + today.getMinutes();
  const nowOffset = ((nowMin / 60) - HOUR_START) * hourHeight;
  const showNow = nowMin >= HOUR_START*60 && nowMin <= 23*60;

  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 2 * hourHeight;
  }, []);

  const isMultiDay = colDays.length > 1;
  const gridCols = `56px repeat(${colDays.length}, 1fr)`;

  return (
    <div className="cal-grid-wrap" ref={scrollRef}>
      <div className="cal-grid" style={{ gridTemplateColumns: gridCols, minWidth: isMultiDay ? 700 : 300 }}>
        <div className="corner cal-grid-head" style={{display:"block"}}></div>
        {colDays.map((d, i) => {
          const isToday = sameDay(d, today);
          return (
            <div key={i} style={{ position:"sticky", top:0, zIndex:5, background:"var(--ink-1)", borderBottom:"1px solid var(--line)"}}>
              {isMultiDay && <div className="dow">{_dowLabels[i]}</div>}
              <div className={"dom " + (isToday ? "today" : "")}>{d.getDate()}</div>
            </div>
          );
        })}
        <div style={{ gridColumn:"1/2", display:"flex", flexDirection:"column"}}>
          {hours.map(h => (
            <div key={h} className="cal-hour-cell">
              <span>{String(h).padStart(2,"0")}:00</span>
            </div>
          ))}
        </div>
        {colDays.map((d, dayIdx) => {
          const isToday = sameDay(d, today);
          const evs = dayEventMap[dayIdx];
          return (
            <div key={dayIdx} className={"cal-day-col" + (isToday ? " today" : "")}>
              {hours.map(h => <div key={h} className="cal-half"/>)}
              {evs.map(ev => {
                const startD = new Date(ev.start);
                const endD = new Date(ev.end);
                const startMin = startD.getHours()*60 + startD.getMinutes() - HOUR_START*60;
                const endMin = endD.getHours()*60 + endD.getMinutes() - HOUR_START*60;
                const top = (startMin / 60) * hourHeight;
                const height = Math.max(((endMin - startMin) / 60) * hourHeight - 2, 22);
                const cols = ev._cols || 1;
                const colIdx = ev._col || 0;
                const widthPct = 100 / cols;
                return (
                  <div
                    key={ev.id}
                    className={"cal-event color-" + (ev.color === "violet" ? "" : ev.color)}
                    style={{ top, height, left:`calc(${colIdx*widthPct}% + 4px)`, width:`calc(${widthPct}% - 8px)` }}
                    onClick={() => onSelectEvent({ event: ev })}
                  >
                    <div className="ev-title">{ev.summary}</div>
                    <div className="ev-time">{fmtTimeVN(ev.start)} – {fmtTimeVN(ev.end)}</div>
                  </div>
                );
              })}
              {isToday && showNow && (
                <div className="cal-now-line" style={{ top: nowOffset }}/>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MonthView({ selected, events, onSelectEvent }) {
  const today = new Date();
  const year = selected.getFullYear();
  const month = selected.getMonth();

  const cells = useMemo(() => {
    const first = new Date(year, month, 1);
    const lead = (first.getDay() + 6) % 7;
    const dim = new Date(year, month+1, 0).getDate();
    const arr = [];
    for (let i=0; i<lead; i++) arr.push({ muted:true, d: new Date(year, month, -lead+i+1) });
    for (let i=1; i<=dim; i++) arr.push({ d: new Date(year, month, i) });
    while (arr.length % 7 !== 0) arr.push({ muted:true, d: new Date(year, month+1, arr.length - lead - dim + 1) });
    return arr;
  }, [year, month]);

  const eventsByDay = useMemo(() => {
    const map = {};
    events.forEach(e => {
      const key = new Date(e.start).toDateString();
      if (!map[key]) map[key] = [];
      map[key].push(e);
    });
    return map;
  }, [events]);

  const colorBg   = { violet:"rgba(167,139,250,.22)", pink:"rgba(244,114,182,.22)", cyan:"rgba(34,211,238,.20)", amber:"rgba(251,191,36,.20)", emerald:"rgba(52,211,153,.20)" };
  const colorLeft = { violet:"#a78bfa", pink:"#f472b6", cyan:"#22d3ee", amber:"#fbbf24", emerald:"#34d399" };

  return (
    <div style={{ flex:1, overflow:"auto" }}>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(7,1fr)", borderTop:"1px solid var(--line)" }}>
        {_dowLabels.map(d => (
          <div key={d} style={{ padding:"8px", textAlign:"center", fontSize:11, fontWeight:600, textTransform:"uppercase", letterSpacing:"0.06em", color:"var(--text-3)", borderBottom:"1px solid var(--line)", borderRight:"1px solid var(--line)" }}>
            {d}
          </div>
        ))}
        {cells.map((c, i) => {
          const isToday = sameDay(c.d, today);
          const dayEvs = eventsByDay[c.d.toDateString()] || [];
          return (
            <div
              key={i}
              onClick={() => onSelectEvent({ selectDay: c.d })}
              style={{ minHeight:90, padding:6, cursor:"pointer", opacity:c.muted?0.4:1, borderBottom:"1px solid var(--line)", borderRight:"1px solid var(--line)" }}
            >
              <div style={{ display:"inline-grid", placeItems:"center", width:22, height:22, borderRadius:"50%", marginBottom:4, fontSize:12.5, fontWeight:600, background:isToday?"var(--grad-brand)":"transparent", color:isToday?"#fff":"var(--text-1)" }}>
                {c.d.getDate()}
              </div>
              {dayEvs.slice(0,3).map(e => (
                <div
                  key={e.id}
                  onClick={ev => { ev.stopPropagation(); onSelectEvent({ event: e }); }}
                  style={{ fontSize:11, padding:"1px 5px", borderRadius:3, marginBottom:1, cursor:"pointer", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis", background:colorBg[e.color]||colorBg.violet, borderLeft:`2px solid ${colorLeft[e.color]||colorLeft.violet}`, color:"var(--text-0)" }}
                >
                  {e.summary}
                </div>
              ))}
              {dayEvs.length > 3 && (
                <div style={{ fontSize:10.5, color:"var(--text-3)", padding:"1px 5px" }}>+{dayEvs.length-3} thêm</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CalendarMain({ selected, events, onSelectEvent, view, onViewChange, onCreate }) {
  const weekStart = useMemo(() => startOfWeek(selected), [selected]);
  const weekDays  = useMemo(() => Array.from({length:7}, (_,i) => addDays(weekStart, i)), [weekStart]);

  let titleLabel;
  if (view === "day") {
    titleLabel = selected.toLocaleDateString("vi-VN", { weekday:"long", day:"2-digit", month:"long", year:"numeric" });
  } else if (view === "week") {
    titleLabel = `${weekDays[0].getDate()} – ${weekDays[6].getDate()} ${_monthLabels[weekDays[6].getMonth()]} ${weekDays[6].getFullYear()}`;
  } else {
    titleLabel = `${_monthLabels[selected.getMonth()]} ${selected.getFullYear()}`;
  }

  const handlePrev = () => {
    if (view === "day")   onSelectEvent({ navDays: -1 });
    else if (view === "week")  onSelectEvent({ navWeek: -1 });
    else                       onSelectEvent({ navMonth: -1 });
  };
  const handleNext = () => {
    if (view === "day")   onSelectEvent({ navDays: +1 });
    else if (view === "week")  onSelectEvent({ navWeek: +1 });
    else                       onSelectEvent({ navMonth: +1 });
  };

  return (
    <div className="module-main">
      <div className="cal-toolbar">
        <div className="cal-title">{titleLabel}</div>
        <div className="cal-nav">
          <button title="Trước" onClick={handlePrev}><I.ChevLeft/></button>
          <button title="Sau" onClick={handleNext} style={{transform:"rotate(180deg)"}}><I.ChevLeft/></button>
        </div>
        <button className="cal-today-btn" onClick={() => onSelectEvent({ today: true })}>Hôm nay</button>
        <div style={{ flex:1 }}/>
        <div className="cal-view-switch">
          <button className={view==="day"  ?"active":""} onClick={() => onViewChange("day")}>Ngày</button>
          <button className={view==="week" ?"active":""} onClick={() => onViewChange("week")}>Tuần</button>
          <button className={view==="month"?"active":""} onClick={() => onViewChange("month")}>Tháng</button>
        </div>
        <button className="cal-create-btn" onClick={onCreate}>
          <I.Plus2/> Tạo sự kiện
        </button>
      </div>

      {view === "day"   && <TimeGrid colDays={[selected]}  events={events} onSelectEvent={onSelectEvent}/>}
      {view === "week"  && <TimeGrid colDays={weekDays}     events={events} onSelectEvent={onSelectEvent}/>}
      {view === "month" && <MonthView selected={selected}   events={events} onSelectEvent={onSelectEvent}/>}
    </div>
  );
}

function EventDetail({ event, onClose, onDelete, onEdit }) {
  if (!event) return null;
  const d = new Date(event.start);
  const dateLabel = d.toLocaleDateString("vi-VN", { weekday:"long", day:"2-digit", month:"long", year:"numeric"});
  const colorMap = { violet:"#a78bfa", pink:"#f472b6", cyan:"#22d3ee", amber:"#fbbf24", emerald:"#34d399"};
  return (
    <div className="cal-detail">
      <div className="cal-detail-head">
        <div className="cal-detail-color" style={{ background: colorMap[event.color] || "#a78bfa"}}/>
        <h3>{event.summary}</h3>
        <button className="icon-btn" onClick={onClose}><I.X/></button>
      </div>
      <div className="cal-detail-meta">
        <div className="cal-detail-row">
          <I.Clock className="icon"/>
          <div>
            <div style={{ textTransform:"capitalize" }}>{dateLabel}</div>
            <div className="muted" style={{ fontSize:12, marginTop:2 }}>
              {fmtTimeVN(event.start)} – {fmtTimeVN(event.end)}
            </div>
          </div>
        </div>
        {event.location && (
          <div className="cal-detail-row">
            <I.Location className="icon"/>
            <div>{event.location}</div>
          </div>
        )}
        {event.attendees && event.attendees.length > 0 && (
          <div className="cal-detail-row">
            <I.Users className="icon"/>
            <div>
              {event.attendees.slice(0,3).map((a,i) => (
                <div key={i} style={{ fontSize:12.5 }}>{a}</div>
              ))}
              {event.attendees.length > 3 && (
                <div className="muted" style={{ fontSize:12, marginTop:2 }}>+{event.attendees.length - 3} người khác</div>
              )}
            </div>
          </div>
        )}
        {event.description && (
          <div className="cal-detail-row">
            <I.Note className="icon"/>
            <div style={{ fontSize:12.5, color:"var(--text-1)"}}>{event.description}</div>
          </div>
        )}
      </div>
      <div className="cal-detail-actions">
        <button className="tb-btn outline" style={{ justifyContent:"center"}} onClick={() => onEdit(event)}>
          <I.Pencil/> Sửa
        </button>
        <button className="tb-btn outline danger" style={{ justifyContent:"center"}} onClick={() => onDelete(event)}>
          <I.Trash/> Xóa
        </button>
      </div>
    </div>
  );
}

const CAL_COLORS = ["violet", "pink", "cyan", "amber", "emerald"];

function EventFormModal({ event, defaultDate, onSave, onClose }) {
  const isEdit = !!event;

  const toLocal = (ms) => {
    const d = new Date(ms);
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const initStart = () => {
    if (event) return toLocal(event.start);
    const d = new Date(defaultDate || Date.now());
    d.setHours(9, 0, 0, 0);
    return toLocal(d.getTime());
  };
  const initEnd = () => {
    if (event) return toLocal(event.end);
    const d = new Date(defaultDate || Date.now());
    d.setHours(10, 0, 0, 0);
    return toLocal(d.getTime());
  };

  const [summary, setSummary]         = useState(event?.summary || "");
  const [startDt, setStartDt]         = useState(initStart);
  const [endDt, setEndDt]             = useState(initEnd);
  const [description, setDescription] = useState(event?.description || "");
  const [location, setLocation]       = useState(event?.location || "");
  const [saving, setSaving]           = useState(false);
  const [error, setError]             = useState("");

  const handle = async (e) => {
    e.preventDefault();
    if (!summary.trim()) { setError("Vui lòng nhập tiêu đề sự kiện"); return; }
    if (new Date(endDt) <= new Date(startDt)) { setError("Thời gian kết thúc phải sau thời gian bắt đầu"); return; }
    setSaving(true);
    setError("");
    try {
      await onSave({
        summary: summary.trim(),
        start_datetime: new Date(startDt).toISOString(),
        end_datetime: new Date(endDt).toISOString(),
        ...(description.trim() && { description: description.trim() }),
        ...(location.trim() && { location: location.trim() }),
      });
    } catch (err) {
      setError(err.message || "Đã có lỗi xảy ra");
      setSaving(false);
    }
  };

  return (
    <div
      style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center" }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div style={{ background:"var(--ink-3)", borderRadius:12, padding:24, border:"1px solid var(--ink-5)", width:460, boxShadow:"0 8px 32px rgba(0,0,0,0.3)" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
          <div style={{ fontWeight:600, fontSize:15 }}>{isEdit ? "Sửa sự kiện" : "Tạo sự kiện mới"}</div>
          <button className="icon-btn" onClick={onClose}><I.X/></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div>
            <label>Tiêu đề *</label>
            <input className="input" type="text" value={summary} onChange={e => setSummary(e.target.value)} placeholder="Tên sự kiện" autoFocus/>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div>
              <label>Bắt đầu</label>
              <input className="input" type="datetime-local" value={startDt} onChange={e => setStartDt(e.target.value)}/>
            </div>
            <div>
              <label>Kết thúc</label>
              <input className="input" type="datetime-local" value={endDt} onChange={e => setEndDt(e.target.value)}/>
            </div>
          </div>
          <div>
            <label>Địa điểm</label>
            <input className="input" type="text" value={location} onChange={e => setLocation(e.target.value)} placeholder="Tuỳ chọn"/>
          </div>
          <div>
            <label>Mô tả</label>
            <textarea className="input" value={description} onChange={e => setDescription(e.target.value)} placeholder="Ghi chú (tuỳ chọn)" rows={3} style={{ resize:"vertical" }}/>
          </div>
          {error && <div style={{ color:"var(--danger)", fontSize:12.5 }}>{error}</div>}
          <div style={{ display:"flex", gap:8, marginTop:4 }}>
            <button type="button" className="submit" style={{ background:"var(--ink-3)", flex:1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex:2 }} disabled={saving}>
              {saving ? "Đang lưu…" : isEdit ? "Cập nhật" : "Tạo sự kiện"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function CalendarModule({ userId }) {
  const [selected, setSelected] = useState(new Date());
  const [view, setView]         = useState("week");
  const [events, setEvents]     = useState([]);
  const [activeEvent, setActiveEvent] = useState(null);
  const [loading, setLoading]   = useState(true);
  const [eventForm, setEventForm] = useState(null); // null | "create" | event object (edit)

  const loadEvents = () => {
    if (!userId) return;
    setLoading(true);
    API.getEvents(userId, 90, 30)
      .then(data => {
        const evs = (data.events || []).map((ev, i) => ({
          id:          ev.event_id,
          summary:     ev.summary,
          start:       new Date(ev.start_datetime).getTime(),
          end:         new Date(ev.end_datetime).getTime(),
          description: ev.description || "",
          location:    ev.location || "",
          attendees:   ev.attendees || [],
          color:       CAL_COLORS[i % CAL_COLORS.length],
        }));
        setEvents(evs);
      })
      .catch(err => console.error("Failed to load events:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadEvents(); }, [userId]);

  useEffect(() => {
    const handler = () => loadEvents();
    window.addEventListener("assistai:refresh:calendar", handler);
    return () => window.removeEventListener("assistai:refresh:calendar", handler);
  }, [userId]);

  const handleEventClick = (payload) => {
    if (payload.event)     { setActiveEvent(payload.event); return; }
    if (payload.navWeek)   { setSelected(d => addDays(d, payload.navWeek * 7)); return; }
    if (payload.navDays)   { setSelected(d => addDays(d, payload.navDays)); return; }
    if (payload.navMonth)  { setSelected(d => addMonths(d, payload.navMonth)); return; }
    if (payload.today)     { setSelected(new Date()); return; }
    if (payload.selectDay) { setSelected(payload.selectDay); return; }
  };

  const handleSaveEvent = async (data) => {
    if (typeof eventForm === "object" && eventForm !== null) {
      await API.updateEvent(userId, eventForm.id, data);
      const updated = {
        ...eventForm,
        summary:     data.summary,
        start:       new Date(data.start_datetime).getTime(),
        end:         new Date(data.end_datetime).getTime(),
        description: data.description || "",
        location:    data.location || "",
      };
      setEvents(prev => prev.map(e => e.id === eventForm.id ? updated : e));
      if (activeEvent?.id === eventForm.id) setActiveEvent(updated);
    } else {
      const res = await API.createEvent(userId, data);
      setEvents(prev => [...prev, {
        id:          res.event_id,
        summary:     data.summary,
        start:       new Date(data.start_datetime).getTime(),
        end:         new Date(data.end_datetime).getTime(),
        description: data.description || "",
        location:    data.location || "",
        color:       CAL_COLORS[prev.length % CAL_COLORS.length],
      }]);
    }
    setEventForm(null);
  };

  const handleDelete = async (ev) => {
    try {
      await API.deleteEvent(userId, ev.id);
      setEvents(prev => prev.filter(e => e.id !== ev.id));
      setActiveEvent(null);
    } catch (err) {
      alert("Không thể xóa sự kiện: " + err.message);
    }
  };

  return (
    <>
      <CalendarSidebar selected={selected} onSelect={setSelected} events={events} onCreate={() => setEventForm("create")}/>
      <div style={{ position:"relative", display:"flex", flexDirection:"column", minWidth:0 }}>
        {loading
          ? <div className="module-main" style={{ alignItems:"center", justifyContent:"center", display:"flex" }}>
              <div style={{ color:"var(--text-3)", fontSize:14 }}>Đang tải lịch…</div>
            </div>
          : <CalendarMain
              selected={selected}
              events={events}
              onSelectEvent={handleEventClick}
              view={view}
              onViewChange={setView}
              onCreate={() => setEventForm("create")}
            />
        }
        {activeEvent && (
          <EventDetail
            event={activeEvent}
            onClose={() => setActiveEvent(null)}
            onDelete={handleDelete}
            onEdit={ev => { setEventForm(ev); setActiveEvent(null); }}
          />
        )}
      </div>
      {eventForm !== null && (
        <EventFormModal
          event={typeof eventForm === "object" ? eventForm : null}
          defaultDate={selected}
          onSave={handleSaveEvent}
          onClose={() => setEventForm(null)}
        />
      )}
    </>
  );
}
