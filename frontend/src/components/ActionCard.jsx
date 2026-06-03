import React from 'react';
import I from './icons';

export function ActionCard({ action, onAccept, onReject }) {
  const typeMap = {
    create_event: { title: "Tạo sự kiện mới",   icon: <I.Calendar2/>, accept: "Thêm vào Calendar" },
    update_event: { title: "Cập nhật sự kiện",   icon: <I.Pencil/>,    accept: "Cập nhật" },
    delete_event: { title: "Xóa sự kiện",         icon: <I.Trash/>,     accept: "Xóa" },
    write_sheet:  { title: "Ghi giao dịch",        icon: <I.Wallet/>,    accept: "Lưu vào Sheet" },
    read_sheet:   { title: "Đọc dữ liệu",          icon: <I.Sheet/>,     accept: "OK" },
  };
  const meta = typeMap[action.type] || typeMap.create_event;
  const isExpense = action.type === "write_sheet";

  const acceptedText = {
    write_sheet:  "Đã ghi vào Google Sheets",
    create_event: "Đã thêm vào Google Calendar",
    update_event: "Đã cập nhật sự kiện",
    delete_event: "Đã xóa sự kiện",
  };

  if (action.status === "accepted") {
    return (
      <div className="action-card">
        <div className="action-head">
          <div className="ico">{meta.icon}</div>
          <div className="title">{meta.title}</div>
          <span className="ai-badge">AI Action</span>
        </div>
        <div className="action-done">
          <I.Check style={{ width: 14, height: 14 }}/>
          {acceptedText[action.type] || "Đã hoàn thành"}
        </div>
      </div>
    );
  }

  if (action.status === "rejected") {
    return (
      <div className="action-card">
        <div className="action-head">
          <div className="ico" style={{ background: "var(--ink-3)", color: "var(--text-2)" }}>{meta.icon}</div>
          <div className="title" style={{ color: "var(--text-2)" }}>{meta.title}</div>
        </div>
        <div className="action-rejected">Đã bỏ qua hành động này.</div>
      </div>
    );
  }

  return (
    <div className="action-card">
      <div className="action-head">
        <div className="ico">{meta.icon}</div>
        <div className="title">{meta.title}</div>
        <span className="ai-badge">AI Action</span>
      </div>
      <div className="action-body">
        {Object.entries(action.data).map(([k, v]) => (
          <div key={k} className="ar">
            <div className="l">{k}</div>
            <div className="v">{v}</div>
          </div>
        ))}
      </div>
      <div className="action-foot">
        <button className="action-btn secondary" onClick={onReject}>
          <I.X/> Bỏ qua
        </button>
        <button className="action-btn primary" onClick={onAccept}>
          <I.Check style={{ width: 13, height: 13 }}/> {meta.accept}
        </button>
      </div>
    </div>
  );
}
