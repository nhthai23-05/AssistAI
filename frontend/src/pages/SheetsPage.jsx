import React, { useState, useMemo, useEffect } from 'react';
import I from '../components/icons';
import API from '../services/api';
import { EXPENSE_CATEGORIES, fmtVND, fmtDateVN } from '../data/expenses';

function SheetsSidebar({ activeFilter, onFilter, categories, expenses, onAddOpen }) {
  const counts = useMemo(() => {
    const m = {};
    expenses.forEach(e => { m[e.category] = (m[e.category] || 0) + 1; });
    return m;
  }, [expenses]);

  return (
    <aside className="sidebar">
      <div className="sb-head">
        <div className="brand">
          <div className="brand-mark"><I.Wallet style={{ width:14, height:14, stroke:"#fff" }}/></div>
          <div className="brand-name"><b>Thu chi</b></div>
        </div>
      </div>

      <button className="new-chat" onClick={onAddOpen} style={{ marginBottom: 14 }}>
        <span className="plus"><I.Plus/></span>
        Thêm giao dịch
        <span className="kbd">⌘E</span>
      </button>

      <div className="sb-section">
        <div className="sb-section-title">Danh mục</div>
      </div>
      <div className="category-filter">
        <div
          className={"cf-item" + (activeFilter === "all" ? " active" : "")}
          onClick={() => onFilter("all")}
        >
          <span className="d" style={{ background:"var(--grad-brand)"}}/>
          Tất cả giao dịch
          <span className="count">{expenses.length}</span>
        </div>
        {categories.map(c => {
          const ct = counts[c.name] || 0;
          if (ct === 0) return null;
          return (
            <div
              key={c.name}
              className={"cf-item" + (activeFilter === c.name ? " active" : "")}
              onClick={() => onFilter(c.name)}
            >
              <span className="d" style={{ background: c.color }}/>
              {c.name}
              <span className="count">{ct}</span>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function SummaryCards({ totalActual, totalPlanned, income, openingBalance, onEditBalance }) {
  const remaining = totalPlanned - totalActual;
  const usedPct = Math.min(100, Math.round((totalActual / totalPlanned) * 100));
  const closingBalance = openingBalance + income - totalActual;
  const savingsThisMonth = closingBalance - openingBalance;
  const savingsPct = openingBalance > 0 ? Math.round((savingsThisMonth / openingBalance) * 100) : 0;

  return (
    <div className="sh-summary">
      <div className="sh-card featured">
        <div className="lbl">Số dư cuối kỳ</div>
        <div className="val">{fmtVND(closingBalance)}</div>
        <div className="sub">
          <span className="delta up"><I.Up/> +{savingsPct}%</span>
          so với đầu kỳ
        </div>
      </div>
      <div className="sh-card" style={{ cursor: "pointer" }} onClick={onEditBalance}>
        <div className="lbl" style={{ display:"flex", alignItems:"center", gap:6 }}>
          Đã chi tháng này
          <span style={{ fontSize:10, color:"var(--text-3)", fontWeight:400 }}>✏️ Sửa số dư</span>
        </div>
        <div className="val">{fmtVND(totalActual)}</div>
        <div className="sub">trên {fmtVND(totalPlanned)} dự kiến</div>
        <div className="balance-bar"><div className="fill" style={{ width: usedPct + "%"}}/></div>
      </div>
      <div className="sh-card">
        <div className="lbl">Thu nhập thực tế</div>
        <div className="val" style={{ color: "var(--success)"}}>{fmtVND(income)}</div>
        <div className="sub">
          <span className="delta up"><I.Up/> +{Math.round(((income-8000000)/8000000)*100)}%</span>
          trên dự kiến
        </div>
      </div>
      <div className="sh-card">
        <div className="lbl">Tiết kiệm tháng này</div>
        <div className="val" style={{ color: remaining >= 0 ? "var(--success)" : "var(--danger)"}}>{fmtVND(savingsThisMonth)}</div>
        <div className="sub">Số dư đầu kỳ: {fmtVND(openingBalance)}</div>
      </div>
    </div>
  );
}

function CategoryBreakdown({ categories, expenses, onEditBudget }) {
  const totals = useMemo(() => {
    const m = {};
    expenses.forEach(e => { m[e.category] = (m[e.category] || 0) + e.amount; });
    return m;
  }, [expenses]);

  const totalActual = useMemo(() => Object.values(totals).reduce((s,v) => s+v, 0), [totals]);
  const rows = categories
    .map(c => ({ ...c, actual: totals[c.name] || 0 }))
    .sort((a,b) => b.actual - a.actual);

  return (
    <div className="sh-panel">
      <div className="sh-panel-head">
        <div className="h">Chi theo danh mục</div>
        <div className="sub">{fmtVND(totalActual)} đã chi · {rows.filter(r => r.actual > 0).length} danh mục</div>
      </div>
      <div className="cat-list">
        {rows.filter(r => r.planned > 0 || r.actual > 0).map(r => {
          const max = Math.max(r.planned, r.actual, 1);
          const actualPct = (r.actual / max) * 100;
          const plannedPct = (r.planned / max) * 100;
          const overBudget = r.actual > r.planned && r.planned > 0;
          const pctOfPlan = r.planned > 0 ? Math.round((r.actual / r.planned) * 100) : null;
          return (
            <div key={r.name} className="cat-row">
              <div className="cat-dot" style={{ background: r.color }}/>
              <div className="cat-info">
                <div className="name">
                  <span>{r.name}</span>
                  <span className="amt-pair">
                    <b>{fmtVND(r.actual)}</b>
                    {r.planned > 0 && <span> / {fmtVND(r.planned)}</span>}
                  </span>
                </div>
                <div className="cat-bar">
                  <div className="fill" style={{ width: actualPct + "%", background: overBudget ? "var(--danger)" : r.color}}/>
                  {r.planned > 0 && r.actual !== r.planned && (
                    <div className="planned-marker" style={{ left: plannedPct + "%"}}/>
                  )}
                </div>
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <div className={"cat-pct" + (overBudget ? " over" : "")}>
                  {pctOfPlan != null ? pctOfPlan + "%" : "—"}
                </div>
                {onEditBudget && (
                  <button
                    className="icon-btn"
                    style={{ fontSize:11, padding:"2px 6px", opacity:0.6 }}
                    onClick={() => onEditBudget(r)}
                    title="Sửa ngân sách"
                  >✏️</button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DonutBudget({ totalActual, totalPlanned }) {
  const r = 60, c = 2 * Math.PI * r;
  const pct = Math.min(1, totalActual / totalPlanned);
  const dashUsed = c * pct;
  const remaining = totalPlanned - totalActual;
  const overspent = remaining < 0;

  return (
    <div className="sh-panel">
      <div className="sh-panel-head">
        <div className="h">Tổng quan ngân sách</div>
        <div className="sub">Tháng này</div>
      </div>
      <div className="donut-wrap">
        <svg className="donut-svg" width="180" height="180" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r={r} fill="none" stroke="var(--ink-4)" strokeWidth="14"/>
          <defs>
            <linearGradient id="donut-grad" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stopColor="#a78bfa"/>
              <stop offset="100%" stopColor="#4f46e5"/>
            </linearGradient>
          </defs>
          <circle
            cx="80" cy="80" r={r} fill="none"
            stroke={overspent ? "var(--danger)" : "url(#donut-grad)"}
            strokeWidth="14"
            strokeDasharray={`${dashUsed} ${c}`}
            strokeLinecap="round"
          />
        </svg>
        <div className="donut-center">
          <div className="num">{Math.round(pct*100)}%</div>
          <div className="lbl">đã dùng</div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6, marginTop:4 }}>
          <div style={{ fontSize: 12, color: "var(--text-2)"}}>Còn lại</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: overspent ? "var(--danger)" : "var(--text-0)", letterSpacing:"-0.01em"}}>
            {fmtVND(remaining)}
          </div>
        </div>
      </div>
    </div>
  );
}

function AddExpenseForm({ categories, onAdd, onClose }) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0,10));
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(categories[0]?.name || "");

  const handle = (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g,""), 10);
    if (!n || !description) return;
    onAdd({ date, amount: n, description, category });
    setAmount(""); setDescription("");
    onClose && onClose();
  };

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g,"");
    return n ? parseInt(n,10).toLocaleString("vi-VN") : "";
  };

  return (
    <div className="sh-panel" style={{ marginBottom: 24 }}>
      <div className="sh-panel-head">
        <div className="h">Thêm giao dịch mới</div>
        <button className="icon-btn" onClick={onClose}><I.X/></button>
      </div>
      <form className="expense-form" onSubmit={handle}>
        <div className="row-2">
          <div>
            <label>Ngày</label>
            <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)}/>
          </div>
          <div>
            <label>Số tiền (VND)</label>
            <div className="amount-input">
              <input
                className="input"
                type="text"
                inputMode="numeric"
                placeholder="0"
                value={fmtInput(amount)}
                onChange={e => setAmount(e.target.value)}
              />
              <span className="suffix">₫</span>
            </div>
          </div>
        </div>
        <div>
          <label>Mô tả</label>
          <input className="input" placeholder="VD: Cơm trưa với team..." value={description} onChange={e => setDescription(e.target.value)}/>
        </div>
        <div>
          <label>Danh mục</label>
          <select value={category} onChange={e => setCategory(e.target.value)}>
            {categories.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
        </div>
        <button type="submit" className="submit">
          Lưu vào Google Sheets
        </button>
      </form>
    </div>
  );
}

function EditExpenseModal({ expense, categories, onSave, onClose }) {
  const [date, setDate] = useState(expense.date);
  const [amount, setAmount] = useState(String(expense.amount));
  const [description, setDescription] = useState(expense.description);
  const [category, setCategory] = useState(expense.category);
  const [saving, setSaving] = useState(false);

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g,"");
    return n ? parseInt(n,10).toLocaleString("vi-VN") : "";
  };

  const handle = async (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g,""), 10);
    if (!n || !description) return;
    setSaving(true);
    await onSave(expense.row_number, { date, amount: n, description, category });
    setSaving(false);
  };

  return (
    <div style={{
      position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000,
      display:"flex", alignItems:"center", justifyContent:"center"
    }}>
      <div style={{
        background:"var(--surface-1)", borderRadius:12, padding:24,
        width:420, boxShadow:"0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <div style={{ fontWeight:600, fontSize:15 }}>Sửa giao dịch (dòng {expense.row_number})</div>
          <button className="icon-btn" onClick={onClose}><I.X/></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div className="row-2">
            <div>
              <label>Ngày</label>
              <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)}/>
            </div>
            <div>
              <label>Số tiền (VND)</label>
              <div className="amount-input">
                <input
                  className="input"
                  type="text"
                  inputMode="numeric"
                  value={fmtInput(amount)}
                  onChange={e => setAmount(e.target.value)}
                />
                <span className="suffix">₫</span>
              </div>
            </div>
          </div>
          <div>
            <label>Mô tả</label>
            <input className="input" value={description} onChange={e => setDescription(e.target.value)}/>
          </div>
          <div>
            <label>Danh mục</label>
            <select value={category} onChange={e => setCategory(e.target.value)}>
              {categories.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
          <div style={{ display:"flex", gap:8, marginTop:4 }}>
            <button type="button" className="submit" style={{ background:"var(--ink-3)", flex:1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex:2 }} disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu thay đổi"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditBalanceModal({ summary, onSave, onClose }) {
  const [opening, setOpening] = useState(String(summary.opening_balance));
  const [closing, setClosing] = useState(String(summary.closing_balance));
  const [saving, setSaving] = useState(false);

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g,"");
    return n ? parseInt(n,10).toLocaleString("vi-VN") : "";
  };

  const parseNum = (v) => parseInt(String(v).replace(/[^\d]/g,""), 10) || 0;

  const handle = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSave({ opening_balance: parseNum(opening), closing_balance: parseNum(closing) });
    setSaving(false);
  };

  return (
    <div style={{
      position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000,
      display:"flex", alignItems:"center", justifyContent:"center"
    }}>
      <div style={{
        background:"var(--surface-1)", borderRadius:12, padding:24,
        width:380, boxShadow:"0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <div style={{ fontWeight:600, fontSize:15 }}>Cập nhật số dư</div>
          <button className="icon-btn" onClick={onClose}><I.X/></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div>
            <label>Số dư đầu kỳ (L8)</label>
            <div className="amount-input">
              <input
                className="input"
                type="text"
                inputMode="numeric"
                value={fmtInput(opening)}
                onChange={e => setOpening(e.target.value)}
              />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div>
            <label>Số dư cuối kỳ (D17)</label>
            <div className="amount-input">
              <input
                className="input"
                type="text"
                inputMode="numeric"
                value={fmtInput(closing)}
                onChange={e => setClosing(e.target.value)}
              />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div style={{ display:"flex", gap:8, marginTop:4 }}>
            <button type="button" className="submit" style={{ background:"var(--ink-3)", flex:1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex:2 }} disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu số dư"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditBudgetModal({ category, onSave, onClose }) {
  const [amount, setAmount] = useState(String(category.planned || 0));
  const [isIncome, setIsIncome] = useState(false);
  const [saving, setSaving] = useState(false);

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g,"");
    return n ? parseInt(n,10).toLocaleString("vi-VN") : "";
  };

  const handle = async (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g,""), 10);
    if (!n) return;
    setSaving(true);
    await onSave({ category: category.name, budget_amount: n, is_income: isIncome });
    setSaving(false);
  };

  return (
    <div style={{
      position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000,
      display:"flex", alignItems:"center", justifyContent:"center"
    }}>
      <div style={{
        background:"var(--surface-1)", borderRadius:12, padding:24,
        width:360, boxShadow:"0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <div style={{ fontWeight:600, fontSize:15 }}>Ngân sách: {category.name}</div>
          <button className="icon-btn" onClick={onClose}><I.X/></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div>
            <label>Ngân sách dự kiến (VND)</label>
            <div className="amount-input">
              <input
                className="input"
                type="text"
                inputMode="numeric"
                value={fmtInput(amount)}
                onChange={e => setAmount(e.target.value)}
              />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <input type="checkbox" id="isIncome" checked={isIncome} onChange={e => setIsIncome(e.target.checked)}/>
            <label htmlFor="isIncome" style={{ cursor:"pointer", marginBottom:0 }}>Đây là danh mục thu nhập</label>
          </div>
          <div style={{ display:"flex", gap:8, marginTop:4 }}>
            <button type="button" className="submit" style={{ background:"var(--ink-3)", flex:1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex:2 }} disabled={saving}>
              {saving ? "Đang lưu..." : "Cập nhật"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ManageCategoriesModal({ categories, userId, onClose, onRefresh }) {
  const [newCat, setNewCat] = useState("");
  const [isIncome, setIsIncome] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newCat.trim()) return;
    setSaving(true);
    try {
      await API.addCategory(userId, { category: newCat.trim(), is_income: isIncome });
      setNewCat("");
      onRefresh();
    } catch (err) {
      alert("Lỗi: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (cat) => {
    if (!confirm(`Xóa danh mục "${cat.name}"?`)) return;
    setDeleting(cat.name);
    try {
      await API.deleteCategory(userId, { category: cat.name, is_income: false });
      onRefresh();
    } catch (err) {
      alert("Lỗi: " + err.message);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div style={{
      position:"fixed", inset:0, background:"rgba(0,0,0,0.5)", zIndex:1000,
      display:"flex", alignItems:"center", justifyContent:"center"
    }}>
      <div style={{
        background:"var(--surface-1)", borderRadius:12, padding:24,
        width:420, maxHeight:"80vh", overflowY:"auto",
        boxShadow:"0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <div style={{ fontWeight:600, fontSize:15 }}>Quản lý danh mục</div>
          <button className="icon-btn" onClick={onClose}><I.X/></button>
        </div>

        <form className="expense-form" onSubmit={handleAdd} style={{ marginBottom:20 }}>
          <div>
            <label>Tên danh mục mới</label>
            <input className="input" value={newCat} onChange={e => setNewCat(e.target.value)} placeholder="VD: Du lịch"/>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <input type="checkbox" id="catIsIncome" checked={isIncome} onChange={e => setIsIncome(e.target.checked)}/>
            <label htmlFor="catIsIncome" style={{ cursor:"pointer", marginBottom:0 }}>Thu nhập</label>
          </div>
          <button type="submit" className="submit" disabled={saving}>
            {saving ? "Đang thêm..." : "+ Thêm danh mục"}
          </button>
        </form>

        <div style={{ borderTop:"1px solid var(--border)", paddingTop:16 }}>
          <div style={{ fontSize:12, color:"var(--text-3)", marginBottom:10 }}>Danh sách hiện tại</div>
          {categories.map(c => (
            <div key={c.name} style={{
              display:"flex", alignItems:"center", gap:8, padding:"6px 0",
              borderBottom:"1px solid var(--ink-4)"
            }}>
              <span style={{ background: c.color, width:8, height:8, borderRadius:"50%", flexShrink:0 }}/>
              <span style={{ flex:1, fontSize:13 }}>{c.name}</span>
              <button
                className="icon-btn"
                style={{ fontSize:11, color:"var(--danger)", opacity: deleting===c.name ? 0.5 : 1 }}
                onClick={() => handleDelete(c)}
                disabled={deleting===c.name}
              >Xóa</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TransactionsTable({ expenses, categories, filter, onEdit, onDelete }) {
  const filtered = useMemo(() => {
    const list = filter === "all" ? expenses : expenses.filter(e => e.category === filter);
    return [...list].sort((a,b) => b.date.localeCompare(a.date));
  }, [expenses, filter]);

  const catMap = useMemo(() => Object.fromEntries(categories.map(c => [c.name, c.color])), [categories]);

  return (
    <div className="sh-panel">
      <div className="sh-panel-head">
        <div className="h">Giao dịch gần đây</div>
        <div className="sub">{filtered.length} giao dịch{filter !== "all" ? ` · ${filter}` : ""}</div>
      </div>
      <div style={{ maxHeight: 380, overflowY: "auto" }}>
        <table className="tx-table">
          <thead>
            <tr>
              <th style={{ width: 80 }}>Ngày</th>
              <th>Mô tả</th>
              <th style={{ width: 160 }}>Danh mục</th>
              <th style={{ width: 130, textAlign:"right" }}>Số tiền</th>
              <th style={{ width: 80, textAlign:"center" }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e, i) => (
              <tr key={i}>
                <td className="muted" style={{ fontVariantNumeric:"tabular-nums" }}>{fmtDateVN(e.date)}</td>
                <td>{e.description}</td>
                <td>
                  <span className="tx-cat-chip">
                    <span className="d" style={{ background: catMap[e.category] || "#a78bfa"}}/>
                    {e.category}
                  </span>
                </td>
                <td className="amt expense">-{fmtVND(e.amount).replace("-","")}</td>
                <td style={{ textAlign:"center" }}>
                  {e.row_number && (
                    <span style={{ display:"flex", gap:4, justifyContent:"center" }}>
                      <button
                        className="icon-btn"
                        style={{ fontSize:11, padding:"2px 5px" }}
                        onClick={() => onEdit(e)}
                        title="Sửa"
                      >✏️</button>
                      <button
                        className="icon-btn"
                        style={{ fontSize:11, padding:"2px 5px", color:"var(--danger)" }}
                        onClick={() => onDelete(e)}
                        title="Xóa"
                      >🗑</button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign:"center", padding:"32px", color:"var(--text-3)"}}>
                  Chưa có giao dịch nào trong danh mục này.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SheetsMain({
  expenses, categories, filter, onAddExpense, addOpen, setAddOpen, summary,
  onEdit, onDelete, onEditBalance, onEditBudget, onManageCategories
}) {
  const totalActual = useMemo(() => expenses.reduce((s,e) => s + e.amount, 0), [expenses]);
  const totalPlanned = useMemo(() => categories.reduce((s,c) => s + c.planned, 0), [categories]);

  return (
    <div className="module-main">
      <div className="sh-toolbar">
        <div className="sh-title">Ngân sách</div>
        <div className="sh-month-pill">
          <I.Calendar2/>
          Tháng {new Date().getMonth() + 1} / {new Date().getFullYear()}
        </div>
        <div style={{ flex: 1 }}/>
        <button className="tb-btn outline" onClick={onManageCategories}>
          Quản lý danh mục
        </button>
        <button className="tb-btn outline">
          <I.Globe style={{ width:14, height:14 }}/> Mở trên Google Sheets
        </button>
        <button className="cal-create-btn" onClick={() => setAddOpen(true)}>
          <I.Plus2/> Thêm giao dịch
        </button>
      </div>

      <div className="sh-content">
        <SummaryCards
          totalActual={totalActual}
          totalPlanned={totalPlanned}
          income={summary.total_income}
          openingBalance={summary.opening_balance}
          onEditBalance={onEditBalance}
        />

        {addOpen && (
          <AddExpenseForm
            categories={categories}
            onAdd={onAddExpense}
            onClose={() => setAddOpen(false)}
          />
        )}

        <div className="sh-row">
          <CategoryBreakdown categories={categories} expenses={expenses} onEditBudget={onEditBudget}/>
          <DonutBudget totalActual={totalActual} totalPlanned={totalPlanned}/>
        </div>

        <TransactionsTable
          expenses={expenses}
          categories={categories}
          filter={filter}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      </div>
    </div>
  );
}

export function SheetsModule({ userId }) {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState(EXPENSE_CATEGORIES);
  const [filter, setFilter] = useState("all");
  const [addOpen, setAddOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({
    opening_balance: 0,
    closing_balance: 0,
    total_expenses: 0,
    total_income: 0,
  });
  const [editingExpense, setEditingExpense] = useState(null);
  const [showBalanceModal, setShowBalanceModal] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [showCategories, setShowCategories] = useState(false);

  const loadData = () => {
    if (!userId) return;
    setLoading(true);
    Promise.all([
      API.getExpenses(userId, 100),
      API.getCategories(userId),
      API.getSummary(userId),
    ])
      .then(([expData, catData, summaryData]) => {
        setExpenses(Array.isArray(expData) ? expData : []);

        const names = (catData.categories || []);
        if (names.length > 0) {
          const merged = names.map(name => {
            const local = EXPENSE_CATEGORIES.find(c => c.name === name);
            return local || { name, color: "#9ca3af", planned: 0 };
          });
          setCategories(merged);
        }

        if (summaryData) {
          setSummary(summaryData);
        }
      })
      .catch(err => console.error("Failed to load sheets data:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, [userId]);

  const handleAdd = async (item) => {
    try {
      await API.addExpense(userId, item);
      setExpenses(prev => [item, ...prev]);
    } catch (err) {
      alert("Không thể lưu giao dịch: " + err.message);
    }
  };

  const handleSaveEdit = async (rowNumber, data) => {
    try {
      const updated = await API.updateExpense(userId, rowNumber, data);
      setExpenses(prev => prev.map(e => e.row_number === rowNumber ? { ...updated, row_number: rowNumber } : e));
      setEditingExpense(null);
    } catch (err) {
      alert("Không thể cập nhật: " + err.message);
    }
  };

  const handleDelete = async (expense) => {
    if (!confirm(`Xóa giao dịch "${expense.description}" (${fmtVND(expense.amount)})?`)) return;
    try {
      await API.deleteExpense(userId, expense.row_number);
      setExpenses(prev => prev.filter(e => e.row_number !== expense.row_number));
    } catch (err) {
      alert("Không thể xóa: " + err.message);
    }
  };

  const handleSaveBalance = async (data) => {
    try {
      await API.updateBalance(userId, data);
      setSummary(prev => ({
        ...prev,
        opening_balance: data.opening_balance ?? prev.opening_balance,
        closing_balance: data.closing_balance ?? prev.closing_balance,
      }));
      setShowBalanceModal(false);
    } catch (err) {
      alert("Không thể cập nhật số dư: " + err.message);
    }
  };

  const handleSaveBudget = async (data) => {
    try {
      await API.updateBudget(userId, data);
      setEditingBudget(null);
    } catch (err) {
      alert("Không thể cập nhật ngân sách: " + err.message);
    }
  };

  return (
    <>
      <SheetsSidebar
        activeFilter={filter}
        onFilter={setFilter}
        categories={categories}
        expenses={expenses}
        onAddOpen={() => setAddOpen(true)}
      />
      <SheetsMain
        expenses={expenses}
        categories={categories}
        filter={filter}
        onAddExpense={handleAdd}
        addOpen={addOpen}
        setAddOpen={setAddOpen}
        summary={summary}
        onEdit={setEditingExpense}
        onDelete={handleDelete}
        onEditBalance={() => setShowBalanceModal(true)}
        onEditBudget={setEditingBudget}
        onManageCategories={() => setShowCategories(true)}
      />

      {editingExpense && (
        <EditExpenseModal
          expense={editingExpense}
          categories={categories}
          onSave={handleSaveEdit}
          onClose={() => setEditingExpense(null)}
        />
      )}

      {showBalanceModal && (
        <EditBalanceModal
          summary={summary}
          onSave={handleSaveBalance}
          onClose={() => setShowBalanceModal(false)}
        />
      )}

      {editingBudget && (
        <EditBudgetModal
          category={editingBudget}
          onSave={handleSaveBudget}
          onClose={() => setEditingBudget(null)}
        />
      )}

      {showCategories && (
        <ManageCategoriesModal
          categories={categories}
          userId={userId}
          onClose={() => setShowCategories(false)}
          onRefresh={loadData}
        />
      )}
    </>
  );
}
