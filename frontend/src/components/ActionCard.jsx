import React from 'react';
import I from './icons';

const FIELD_LABELS = {
  date: "Ngày", amount: "Số tiền", description: "Mô tả", category: "Danh mục",
  summary: "Tiêu đề", start_datetime: "Bắt đầu", end_datetime: "Kết thúc",
  location: "Địa điểm",
};

function formatAmount(v) {
  if (typeof v === "number") return v.toLocaleString("vi-VN") + " ₫";
  return v;
}

function formatDatetime(raw) {
  if (!raw) return "";
  try {
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return raw;
    const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(raw);
    if (isDateOnly) {
      return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
    }
    return d.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return raw;
  }
}

function DeleteEventPreview({ data }) {
  return (
    <>
      <div className="ar">
        <div className="l">Sự kiện</div>
        <div className="v">{data.event_summary || "—"}</div>
      </div>
      {data.start_datetime && (
        <div className="ar">
          <div className="l">Bắt đầu</div>
          <div className="v">{formatDatetime(data.start_datetime)}</div>
        </div>
      )}
      {data.end_datetime && (
        <div className="ar">
          <div className="l">Kết thúc</div>
          <div className="v">{formatDatetime(data.end_datetime)}</div>
        </div>
      )}
    </>
  );
}

function FieldRow({ k, v }) {
  const label = FIELD_LABELS[k] || k;
  const display = k === "amount" ? formatAmount(v) : String(v ?? "");
  if (!display) return null;
  return (
    <div className="ar">
      <div className="l">{label}</div>
      <div className="v">{display}</div>
    </div>
  );
}

function ExpenseTable({ items }) {
  const total = items.reduce((s, x) => s + (x.amount || 0), 0);
  return (
    <div className="action-table-wrap">
      <table className="action-table">
        <thead>
          <tr>
            <th>Ngày</th>
            <th>Mô tả</th>
            <th>Danh mục</th>
            <th style={{ textAlign: "right" }}>Số tiền</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={i}>
              <td>{item.date || "—"}</td>
              <td>{item.description || "—"}</td>
              <td>{item.category || "—"}</td>
              <td style={{ textAlign: "right" }}>{formatAmount(item.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={3} style={{ textAlign: "right", fontWeight: 600 }}>Tổng</td>
            <td style={{ textAlign: "right", fontWeight: 600 }}>{formatAmount(total)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export function ActionCard({ action, onAccept, onReject }) {
  const isMultiExpense = action.type === "write_sheet" && Array.isArray(action.data);
  const multiCount = isMultiExpense ? action.data.length : 1;

  const isMultiIncome = action.type === "write_income_sheet" && Array.isArray(action.data);
  const incomeCount = isMultiIncome ? action.data.length : 1;

  const typeMap = {
    create_event:       { title: "Tạo sự kiện mới",                                    icon: <I.Calendar2/>, accept: "Thêm vào Calendar" },
    update_event:       { title: "Cập nhật sự kiện",                                   icon: <I.Pencil/>,    accept: "Cập nhật" },
    delete_event:       { title: "Xóa sự kiện",                                        icon: <I.Trash/>,     accept: "Xóa" },
    write_sheet:        { title: isMultiExpense ? `Ghi ${multiCount} khoản chi` : "Ghi khoản chi",   icon: <I.Wallet/>, accept: "Lưu vào Sheet" },
    write_income_sheet: { title: isMultiIncome  ? `Ghi ${incomeCount} khoản thu` : "Ghi khoản thu", icon: <I.Wallet/>, accept: "Lưu vào Sheet" },
    read_sheet:         { title: "Đọc dữ liệu",                                        icon: <I.Sheet/>,     accept: "OK" },
  };
  const meta = typeMap[action.type] || typeMap.create_event;

  const acceptedText = {
    write_sheet:        isMultiExpense
      ? `Đã ghi ${multiCount} khoản chi vào Google Sheets`
      : "Đã ghi khoản chi vào Google Sheets",
    write_income_sheet: isMultiIncome
      ? `Đã ghi ${incomeCount} khoản thu vào Google Sheets`
      : "Đã ghi khoản thu vào Google Sheets",
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
        {isMultiExpense ? (
          <ExpenseTable items={action.data} />
        ) : action.type === "delete_event" ? (
          <DeleteEventPreview data={action.data || {}} />
        ) : (
          Object.entries(action.data || {}).map(([k, v]) => (
            <FieldRow key={k} k={k} v={v} />
          ))
        )}
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
