import React, { useState } from 'react';
import I from '../components/icons';

export function SettingsModule({ onLogout, userEmail }) {
  const [notifications, setNotifications] = useState(true);
  const [autoSync, setAutoSync] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [streaming, setStreaming] = useState(true);
  const [activeSection, setActiveSection] = useState("account");

  const displayName = userEmail ? userEmail.split("@")[0] : "Người dùng";
  const initials = displayName.slice(0, 2).toUpperCase();

  const navItems = [
    { id: "account",       icon: <I.Users style={{ width:14, height:14 }}/>,   label: "Tài khoản" },
    { id: "integrations",  icon: <I.Globe style={{ width:14, height:14 }}/>,   label: "Tích hợp" },
    { id: "model",         icon: <I.Sparkle style={{ width:14, height:14 }}/>, label: "Mô hình AI" },
    { id: "notifications", icon: <I.Bell style={{ width:14, height:14 }}/>,    label: "Thông báo" },
  ];

  return (
    <>
      <aside className="sidebar">
        <div className="sb-head">
          <div className="brand">
            <div className="brand-mark"><I.Settings style={{ width:14, height:14, stroke:"#fff" }}/></div>
            <div className="brand-name"><b>Cài đặt</b></div>
          </div>
        </div>
        <div className="sb-list">
          <div className="sb-section"><div className="sb-section-title">Mục</div></div>
          <div className="category-filter">
            {navItems.map(item => (
              <div key={item.id} className={"cf-item" + (activeSection === item.id ? " active" : "")} onClick={() => setActiveSection(item.id)} style={{ cursor: "pointer" }}>
                {item.icon} {item.label}
              </div>
            ))}
          </div>
        </div>
      </aside>
      <div className="module-main">
        <div className="topbar">
          <div className="title"><span className="title-text">Cài đặt</span></div>
        </div>
        <div className="module-scroll">
          <div className="settings-page">
            <h1>Cài đặt</h1>
            <p className="sub">Quản lý tài khoản, dịch vụ kết nối và tùy chỉnh trợ lý của bạn.</p>

            {activeSection === "account" && (
              <div className="set-section">
                <div className="set-section-head"><h2>Tài khoản</h2><p>Thông tin đăng nhập Google của bạn</p></div>
                <div className="set-row">
                  <div className="avatar" style={{ width: 44, height: 44, fontSize: 14 }}>{initials}</div>
                  <div className="body"><div className="lbl">{displayName}</div><div className="desc">{userEmail || "—"} · Đã xác minh</div></div>
                  <button className="tb-btn outline" onClick={onLogout}><I.Logout/> Đăng xuất</button>
                </div>
              </div>
            )}

            {activeSection === "integrations" && (
              <div className="set-section">
                <div className="set-section-head"><h2>Dịch vụ kết nối</h2><p>Cấp quyền OAuth cho Google Calendar và Google Sheets</p></div>
                <div className="set-row">
                  <div className="ico"><I.Calendar2/></div>
                  <div className="body"><div className="lbl">Google Calendar</div><div className="desc">Đọc, tạo, sửa, xóa sự kiện</div></div>
                  <span className="status-ok"><I.Check style={{ width:12, height:12 }}/> Đã kết nối</span>
                </div>
                <div className="set-row">
                  <div className="ico"><I.Sheet/></div>
                  <div className="body"><div className="lbl">Google Sheets</div><div className="desc">Đọc và ghi giao dịch thu chi</div></div>
                  <span className="status-ok"><I.Check style={{ width:12, height:12 }}/> Đã kết nối</span>
                </div>
                <div className="set-row">
                  <div className="ico"><I.Sparkle/></div>
                  <div className="body"><div className="lbl">OpenAI API</div><div className="desc">Kết nối qua biến môi trường LLM_API_KEY</div></div>
                  <span className="status-ok"><I.Check style={{ width:12, height:12 }}/> Đã cấu hình</span>
                </div>
              </div>
            )}

            {activeSection === "model" && (
              <div className="set-section">
                <div className="set-section-head"><h2>Mô hình AI</h2><p>Tùy chỉnh hành vi trợ lý</p></div>
                <div className="set-row">
                  <div className="ico"><I.Lightning/></div>
                  <div className="body"><div className="lbl">Streaming responses</div><div className="desc">Hiển thị từng từ khi AI đang trả lời</div></div>
                  <div className={"toggle" + (streaming ? " on" : "")} onClick={() => setStreaming(!streaming)}/>
                </div>
                <div className="set-row">
                  <div className="ico"><I.Brain/></div>
                  <div className="body"><div className="lbl">Ngữ cảnh cuộc trò chuyện</div><div className="desc">Cho phép AI nhớ các tin nhắn trước trong session</div></div>
                  <div className="toggle on"/>
                </div>
              </div>
            )}

            {activeSection === "notifications" && (
              <div className="set-section">
                <div className="set-section-head"><h2>Thông báo & Đồng bộ</h2><p>Cảnh báo sự kiện sắp tới và tự động đồng bộ dữ liệu</p></div>
                <div className="set-row">
                  <div className="ico"><I.Bell/></div>
                  <div className="body"><div className="lbl">Thông báo sự kiện</div><div className="desc">Nhắc nhở 15 phút trước khi sự kiện bắt đầu</div></div>
                  <div className={"toggle" + (notifications ? " on" : "")} onClick={() => setNotifications(!notifications)}/>
                </div>
                <div className="set-row">
                  <div className="ico"><I.Refresh/></div>
                  <div className="body"><div className="lbl">Tự động đồng bộ</div><div className="desc">Đồng bộ Calendar và Sheets mỗi 5 phút</div></div>
                  <div className={"toggle" + (autoSync ? " on" : "")} onClick={() => setAutoSync(!autoSync)}/>
                </div>
                <div className="set-row">
                  <div className="ico"><I.Image/></div>
                  <div className="body"><div className="lbl">Chế độ tối</div><div className="desc">Giao diện tối — dễ chịu với mắt vào ban đêm</div></div>
                  <div className={"toggle" + (darkMode ? " on" : "")} onClick={() => setDarkMode(!darkMode)}/>
                </div>
              </div>
            )}

            <div style={{ textAlign:"center", color:"var(--text-3)", fontSize: 11.5, marginTop: 20 }}>
              AssistAI Desktop · v0.1.0 · Backend kết nối: localhost:8000
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
