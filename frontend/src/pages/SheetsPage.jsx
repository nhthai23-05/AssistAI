import React, { useState, useMemo, useEffect } from 'react';
import I from '../components/icons';
import API from '../services/api';
import { EXPENSE_CATEGORIES, fmtVND, fmtDateVN } from '../data/expenses';

const INCOME_COLOR = "#16a34a";

function TabToggle({ activeTab, onChange }) {
  const btn = (tab, icon, label) => (
    <button
      onClick={() => onChange(tab)}
      style={{
        padding: "7px 20px",
        borderRadius: 8,
        border: "none",
        cursor: "pointer",
        fontWeight: 600,
        fontSize: 13,
        transition: "all .15s",
        background: activeTab === tab
          ? (tab === "thu" ? "#16a34a33" : "var(--ink-5)")
          : "transparent",
        color: activeTab === tab
          ? (tab === "thu" ? INCOME_COLOR : "var(--text-0)")
          : "var(--text-3)",
        display: "flex", alignItems: "center", gap: 5,
      }}
    >
      <span style={{ fontSize: 12 }}>{icon}</span> {label}
    </button>
  );
  return (
    <div style={{
      display: "flex", background: "var(--ink-3)", borderRadius: 10,
      padding: 3, gap: 2, border: "1px solid var(--ink-5)",
    }}>
      {btn("chi", "↘", "Chi tiêu")}
      {btn("thu", "↗", "Thu nhập")}
    </div>
  );
}

function SheetsSidebar({ activeTab, onTabChange, activeFilter, onFilter, categories, incomeCategories, expenseItems, incomeItems, onAddOpen }) {
  const expenseCounts = useMemo(() => {
    const m = {};
    expenseItems.forEach(e => { m[e.category] = (m[e.category] || 0) + 1; });
    return m;
  }, [expenseItems]);

  const incomeCounts = useMemo(() => {
    const m = {};
    incomeItems.forEach(e => { m[e.category] = (m[e.category] || 0) + 1; });
    return m;
  }, [incomeItems]);

  const isIncome = activeTab === "thu";
  const showCounts = isIncome ? incomeCounts : expenseCounts;
  const showItems = isIncome ? incomeItems : expenseItems;
  const showCategories = isIncome
    ? incomeCategories.map(n => ({ name: n, color: INCOME_COLOR }))
    : categories;

  return (
    <aside className="sidebar">
      <div className="sb-head">
        <div className="brand">
          <div className="brand-mark"><I.Wallet style={{ width: 14, height: 14, stroke: "#fff" }} /></div>
          <div className="brand-name"><b>Thu chi</b></div>
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <TabToggle activeTab={activeTab} onChange={onTabChange} />
      </div>

      <button className="new-chat" onClick={onAddOpen} style={{ marginBottom: 14 }}>
        <span className="plus"><I.Plus /></span>
        {isIncome ? "Thêm thu nhập" : "Thêm chi tiêu"}
        <span className="kbd">⌘E</span>
      </button>

      <div className="sb-section">
        <div className="sb-section-title">{isIncome ? "Danh mục thu" : "Danh mục chi"}</div>
      </div>
      <div className="category-filter">
        <div
          className={"cf-item" + (activeFilter === "all" ? " active" : "")}
          onClick={() => onFilter("all")}
        >
          <span className="d" style={{ background: isIncome ? INCOME_COLOR : "var(--grad-brand)" }} />
          {isIncome ? "Tất cả thu nhập" : "Tất cả chi tiêu"}
          <span className="count">{showItems.length}</span>
        </div>
        {showCategories.map(c => {
          const ct = showCounts[c.name] || 0;
          if (ct === 0) return null;
          return (
            <div
              key={c.name}
              className={"cf-item" + (activeFilter === c.name ? " active" : "")}
              onClick={() => onFilter(c.name)}
            >
              <span className="d" style={{ background: c.color }} />
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
          <span className="delta up"><I.Up /> +{savingsPct}%</span>
          so với đầu kỳ
        </div>
      </div>
      <div className="sh-card" style={{ cursor: "pointer" }} onClick={onEditBalance}>
        <div className="lbl" style={{ display: "flex", alignItems: "center", gap: 6 }}>
          Đã chi tháng này
          <span style={{ fontSize: 10, color: "var(--text-3)", fontWeight: 400 }}>✏️ Sửa số dư</span>
        </div>
        <div className="val">{fmtVND(totalActual)}</div>
        <div className="sub">trên {fmtVND(totalPlanned)} dự kiến</div>
        <div className="balance-bar"><div className="fill" style={{ width: usedPct + "%" }} /></div>
      </div>
      <div className="sh-card">
        <div className="lbl">Thu nhập thực tế</div>
        <div className="val" style={{ color: "var(--success)" }}>{fmtVND(income)}</div>
        <div className="sub">
          <span className="delta up"><I.Up /> +{Math.round(((income - 8000000) / 8000000) * 100)}%</span>
          trên dự kiến
        </div>
      </div>
      <div className="sh-card">
        <div className="lbl">Tiết kiệm tháng này</div>
        <div className="val" style={{ color: remaining >= 0 ? "var(--success)" : "var(--danger)" }}>{fmtVND(savingsThisMonth)}</div>
        <div className="sub">Số dư đầu kỳ: {fmtVND(openingBalance)}</div>
      </div>
    </div>
  );
}

function IncomeSummaryCards({ incomeBudgets, openingBalance }) {
  const totalActual = useMemo(() => incomeBudgets.reduce((s, b) => s + b.actual, 0), [incomeBudgets]);
  const totalPlanned = useMemo(() => incomeBudgets.reduce((s, b) => s + b.planned, 0), [incomeBudgets]);
  const topCat = useMemo(() => {
    const sorted = [...incomeBudgets].sort((a, b) => b.actual - a.actual);
    return sorted[0]?.actual > 0 ? sorted[0] : null;
  }, [incomeBudgets]);
  const activeCats = incomeBudgets.filter(b => b.actual > 0).length;

  return (
    <div className="sh-summary">
      <div className="sh-card featured" style={{ borderColor: "#16a34a44" }}>
        <div className="lbl">Tổng thu nhập thực tế</div>
        <div className="val" style={{ color: "var(--success)" }}>{fmtVND(totalActual)}</div>
        <div className="sub">Dự kiến: {fmtVND(totalPlanned)}</div>
      </div>
      <div className="sh-card">
        <div className="lbl">Số dư đầu kỳ</div>
        <div className="val">{fmtVND(openingBalance)}</div>
        <div className="sub">Tháng {new Date().getMonth() + 1} / {new Date().getFullYear()}</div>
      </div>
      <div className="sh-card">
        <div className="lbl">Danh mục nhiều nhất</div>
        <div className="val" style={{ fontSize: 15, color: topCat ? "var(--success)" : "var(--text-3)" }}>
          {topCat ? topCat.name : "—"}
        </div>
        <div className="sub">{topCat ? fmtVND(topCat.actual) : "Chưa có thu nhập"}</div>
      </div>
      <div className="sh-card">
        <div className="lbl">Danh mục có thu nhập</div>
        <div className="val">{activeCats}</div>
        <div className="sub">trong kỳ này</div>
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

  const totalActual = useMemo(() => Object.values(totals).reduce((s, v) => s + v, 0), [totals]);
  const rows = categories
    .map(c => ({ ...c, actual: totals[c.name] || 0 }))
    .sort((a, b) => b.actual - a.actual);

  return (
    <div className="sh-panel">
      <div className="sh-panel-head">
        <div className="h">Chi theo danh mục</div>
        <div className="sub">{fmtVND(totalActual)} đã chi · {rows.filter(r => r.actual > 0).length} danh mục</div>
      </div>
      <div className="cat-list">
        {rows.map(r => {
          const max = Math.max(r.planned, r.actual, 1);
          const actualPct = (r.actual / max) * 100;
          const plannedPct = (r.planned / max) * 100;
          const overBudget = r.actual > r.planned && r.planned > 0;
          const pctOfPlan = r.planned > 0 ? Math.round((r.actual / r.planned) * 100) : null;
          return (
            <div key={r.name} className="cat-row">
              <div className="cat-dot" style={{ background: r.color }} />
              <div className="cat-info">
                <div className="name">
                  <span>{r.name}</span>
                  <span className="amt-pair">
                    <b>{fmtVND(r.actual)}</b>
                    {r.planned > 0 && <span> / {fmtVND(r.planned)}</span>}
                  </span>
                </div>
                <div className="cat-bar">
                  <div className="fill" style={{ width: actualPct + "%", background: overBudget ? "var(--danger)" : r.color }} />
                  {r.planned > 0 && r.actual !== r.planned && (
                    <div className="planned-marker" style={{ left: plannedPct + "%" }} />
                  )}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div className={"cat-pct" + (overBudget ? " over" : "")}>
                  {pctOfPlan != null ? pctOfPlan + "%" : "—"}
                </div>
                {onEditBudget && (
                  <button
                    className="icon-btn"
                    style={{ fontSize: 11, padding: "2px 6px", opacity: 0.6 }}
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

function IncomeCategoryBreakdown({ incomeBudgets, onEditBudget }) {
  const totalActual = useMemo(() => incomeBudgets.reduce((s, b) => s + b.actual, 0), [incomeBudgets]);
  const totalPlanned = useMemo(() => incomeBudgets.reduce((s, b) => s + b.planned, 0), [incomeBudgets]);

  return (
    <div className="sh-panel" style={{ flex: 1 }}>
      <div className="sh-panel-head">
        <div className="h">Thu theo danh mục</div>
        <div className="sub">{fmtVND(totalActual)} thực tế · {fmtVND(totalPlanned)} dự kiến</div>
      </div>
      <div className="cat-list">
        {incomeBudgets.map(b => {
          const max = Math.max(b.planned, b.actual, 1);
          const actualPct = (b.actual / max) * 100;
          const plannedPct = (b.planned / max) * 100;
          const overPlan = b.actual > b.planned && b.planned > 0;
          const pctOfPlan = b.planned > 0 ? Math.round((b.actual / b.planned) * 100) : null;
          return (
            <div key={b.name} className="cat-row">
              <div className="cat-dot" style={{ background: INCOME_COLOR }} />
              <div className="cat-info">
                <div className="name">
                  <span>{b.name}</span>
                  <span className="amt-pair">
                    <b style={{ color: b.actual > 0 ? "var(--success)" : "var(--text-3)" }}>{fmtVND(b.actual)}</b>
                    {b.planned > 0 && <span> / {fmtVND(b.planned)}</span>}
                  </span>
                </div>
                <div className="cat-bar">
                  <div className="fill" style={{ width: actualPct + "%", background: overPlan ? "#22c55e" : INCOME_COLOR }} />
                  {b.planned > 0 && b.actual !== b.planned && (
                    <div className="planned-marker" style={{ left: plannedPct + "%" }} />
                  )}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div className="cat-pct">{pctOfPlan != null ? pctOfPlan + "%" : "—"}</div>
                {onEditBudget && (
                  <button
                    className="icon-btn"
                    style={{ fontSize: 11, padding: "2px 6px", opacity: 0.6 }}
                    onClick={() => onEditBudget({ name: b.name, color: INCOME_COLOR, planned: b.planned })}
                    title="Sửa ngân sách"
                  >✏️</button>
                )}
              </div>
            </div>
          );
        })}
        {incomeBudgets.length === 0 && (
          <div style={{ textAlign: "center", padding: "24px", color: "var(--text-3)", fontSize: 13 }}>
            Chưa có danh mục thu nhập.
          </div>
        )}
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
          <circle cx="80" cy="80" r={r} fill="none" stroke="var(--ink-4)" strokeWidth="14" />
          <defs>
            <linearGradient id="donut-grad" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stopColor="#a78bfa" />
              <stop offset="100%" stopColor="#4f46e5" />
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
          <div className="num">{Math.round(pct * 100)}%</div>
          <div className="lbl">đã dùng</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, marginTop: 4 }}>
          <div style={{ fontSize: 12, color: "var(--text-2)" }}>Còn lại</div>
          <div style={{ fontSize: 18, fontWeight: 600, color: overspent ? "var(--danger)" : "var(--text-0)", letterSpacing: "-0.01em" }}>
            {fmtVND(remaining)}
          </div>
        </div>
      </div>
    </div>
  );
}

function AddTransactionForm({ categories, isIncome, onAdd, onClose }) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState(() => {
    const first = categories[0];
    return typeof first === "string" ? first : first?.name || "";
  });

  useEffect(() => {
    const first = categories[0];
    setCategory(typeof first === "string" ? first : first?.name || "");
  }, [isIncome]);

  const handle = (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g, ""), 10);
    if (!n || !description) return;
    const catName = typeof category === "string" ? category : category?.name || "";
    onAdd({ date, amount: n, description, category: catName });
    setAmount("");
    setDescription("");
    onClose && onClose();
  };

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g, "");
    return n ? parseInt(n, 10).toLocaleString("vi-VN") : "";
  };

  return (
    <div className="sh-panel" style={{ marginBottom: 24, borderColor: isIncome ? "#16a34a44" : undefined }}>
      <div className="sh-panel-head">
        <div className="h" style={{ color: isIncome ? "var(--success)" : undefined }}>
          {isIncome ? "↗ Thêm thu nhập" : "↘ Thêm chi tiêu"}
        </div>
        <button className="icon-btn" onClick={onClose}><I.X /></button>
      </div>
      <form className="expense-form" onSubmit={handle}>
        <div className="row-2">
          <div>
            <label>Ngày</label>
            <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)} />
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
          <input
            className="input"
            placeholder={isIncome ? "VD: Lương tháng 6..." : "VD: Cơm trưa với team..."}
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </div>
        <div>
          <label>Danh mục</label>
          <select value={category} onChange={e => setCategory(e.target.value)}>
            {categories.map(c => {
              const name = typeof c === "string" ? c : c.name;
              return <option key={name} value={name}>{name}</option>;
            })}
          </select>
        </div>
        <button
          type="submit"
          className="submit"
          style={isIncome ? { background: "linear-gradient(135deg, #4ade80, #16a34a)" } : undefined}
        >
          {isIncome ? "↗ Lưu thu nhập" : "Lưu vào Google Sheets"}
        </button>
      </form>
    </div>
  );
}

function EditExpenseModal({ expense, categories, isIncome, onSave, onClose }) {
  const [date, setDate] = useState(expense.date);
  const [amount, setAmount] = useState(String(expense.amount));
  const [description, setDescription] = useState(expense.description);
  const [category, setCategory] = useState(expense.category);
  const [saving, setSaving] = useState(false);

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g, "");
    return n ? parseInt(n, 10).toLocaleString("vi-VN") : "";
  };

  const handle = async (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g, ""), 10);
    if (!n || !description) return;
    setSaving(true);
    await onSave(expense.row_number, { date, amount: n, description, category });
    setSaving(false);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center"
    }}>
      <div style={{
        background: "var(--ink-3)", borderRadius: 12, padding: 24, border: "1px solid var(--ink-5)",
        width: 420, boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 15 }}>
            {isIncome ? "Sửa thu nhập" : "Sửa chi tiêu"} (dòng {expense.row_number})
          </div>
          <button className="icon-btn" onClick={onClose}><I.X /></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div className="row-2">
            <div>
              <label>Ngày</label>
              <input className="input" type="date" value={date} onChange={e => setDate(e.target.value)} />
            </div>
            <div>
              <label>Số tiền (VND)</label>
              <div className="amount-input">
                <input
                  className="input" type="text" inputMode="numeric"
                  value={fmtInput(amount)} onChange={e => setAmount(e.target.value)}
                />
                <span className="suffix">₫</span>
              </div>
            </div>
          </div>
          <div>
            <label>Mô tả</label>
            <input className="input" value={description} onChange={e => setDescription(e.target.value)} />
          </div>
          <div>
            <label>Danh mục</label>
            <select value={category} onChange={e => setCategory(e.target.value)}>
              {categories.map(c => {
                const name = typeof c === "string" ? c : c.name;
                return <option key={name} value={name}>{name}</option>;
              })}
            </select>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <button type="button" className="submit" style={{ background: "var(--ink-3)", flex: 1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex: 2 }} disabled={saving}>
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
    const n = String(v).replace(/[^\d]/g, "");
    return n ? parseInt(n, 10).toLocaleString("vi-VN") : "";
  };
  const parseNum = (v) => parseInt(String(v).replace(/[^\d]/g, ""), 10) || 0;

  const handle = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSave({ opening_balance: parseNum(opening), closing_balance: parseNum(closing) });
    setSaving(false);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center"
    }}>
      <div style={{
        background: "var(--ink-3)", borderRadius: 12, padding: 24, border: "1px solid var(--ink-5)",
        width: 380, boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 15 }}>Cập nhật số dư</div>
          <button className="icon-btn" onClick={onClose}><I.X /></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div>
            <label>Số dư đầu kỳ (L8)</label>
            <div className="amount-input">
              <input className="input" type="text" inputMode="numeric" value={fmtInput(opening)} onChange={e => setOpening(e.target.value)} />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div>
            <label>Số dư cuối kỳ (D17)</label>
            <div className="amount-input">
              <input className="input" type="text" inputMode="numeric" value={fmtInput(closing)} onChange={e => setClosing(e.target.value)} />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <button type="button" className="submit" style={{ background: "var(--ink-3)", flex: 1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex: 2 }} disabled={saving}>
              {saving ? "Đang lưu..." : "Lưu số dư"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditBudgetModal({ category, isIncome, onSave, onClose }) {
  const [amount, setAmount] = useState(String(category.planned || 0));
  const [saving, setSaving] = useState(false);

  const fmtInput = (v) => {
    const n = String(v).replace(/[^\d]/g, "");
    return n ? parseInt(n, 10).toLocaleString("vi-VN") : "";
  };

  const handle = async (e) => {
    e.preventDefault();
    const n = parseInt(String(amount).replace(/[^\d]/g, ""), 10);
    if (isNaN(n) || n < 0) return;
    setSaving(true);
    await onSave({ category: category.name, budget_amount: n, is_income: isIncome });
    setSaving(false);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center"
    }}>
      <div style={{
        background: "var(--ink-3)", borderRadius: 12, padding: 24, border: "1px solid var(--ink-5)",
        width: 360, boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 15 }}>
            Ngân sách {isIncome ? "thu" : "chi"}: {category.name}
          </div>
          <button className="icon-btn" onClick={onClose}><I.X /></button>
        </div>
        <form className="expense-form" onSubmit={handle}>
          <div>
            <label>Ngân sách dự kiến (VND)</label>
            <div className="amount-input">
              <input className="input" type="text" inputMode="numeric" value={fmtInput(amount)} onChange={e => setAmount(e.target.value)} />
              <span className="suffix">₫</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <button type="button" className="submit" style={{ background: "var(--ink-3)", flex: 1 }} onClick={onClose}>Hủy</button>
            <button type="submit" className="submit" style={{ flex: 2 }} disabled={saving}>
              {saving ? "Đang lưu..." : "Cập nhật"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ManageCategoriesModal({ categories, userId, isIncome, onClose, onRefresh }) {
  const [newCat, setNewCat] = useState("");
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
      await API.deleteCategory(userId, { category: cat.name, is_income: isIncome });
      onRefresh();
    } catch (err) {
      alert("Lỗi: " + err.message);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center"
    }}>
      <div style={{
        background: "var(--ink-3)", borderRadius: 12, padding: 24, border: "1px solid var(--ink-5)",
        width: 420, maxHeight: "80vh", overflowY: "auto",
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 15 }}>
            Danh mục {isIncome ? "Thu nhập" : "Chi tiêu"}
          </div>
          <button className="icon-btn" onClick={onClose}><I.X /></button>
        </div>

        <form className="expense-form" onSubmit={handleAdd} style={{ marginBottom: 20 }}>
          <div>
            <label>Tên danh mục mới</label>
            <input
              className="input"
              value={newCat}
              onChange={e => setNewCat(e.target.value)}
              placeholder={isIncome ? "VD: Lương, Freelance..." : "VD: Du lịch, Ăn uống..."}
            />
          </div>
          <button type="submit" className="submit" disabled={saving}
            style={isIncome ? { background: "linear-gradient(135deg, #4ade80, #16a34a)" } : undefined}
          >
            {saving ? "Đang thêm..." : `+ Thêm danh mục ${isIncome ? "thu" : "chi"}`}
          </button>
        </form>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16 }}>
          <div style={{ fontSize: 12, color: "var(--text-3)", marginBottom: 10 }}>Danh sách hiện tại</div>
          {categories.map(c => (
            <div key={c.name} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "6px 0",
              borderBottom: "1px solid var(--ink-4)"
            }}>
              <span style={{ background: c.color, width: 8, height: 8, borderRadius: "50%", flexShrink: 0 }} />
              <span style={{ flex: 1, fontSize: 13 }}>{c.name}</span>
              <button
                className="icon-btn"
                style={{ fontSize: 11, color: "var(--danger)", opacity: deleting === c.name ? 0.5 : 1 }}
                onClick={() => handleDelete(c)}
                disabled={deleting === c.name}
              >Xóa</button>
            </div>
          ))}
          {categories.length === 0 && (
            <div style={{ textAlign: "center", padding: "16px", color: "var(--text-3)", fontSize: 13 }}>
              Chưa có danh mục nào
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TransactionsTable({ expenses, categories, filter, isIncome, onEdit, onDelete }) {
  const filtered = useMemo(() => {
    const list = filter === "all" ? expenses : expenses.filter(e => e.category === filter);
    return [...list].sort((a, b) => b.date.localeCompare(a.date));
  }, [expenses, filter]);

  const catMap = useMemo(() => Object.fromEntries(categories.map(c => [c.name || c, c.color || (isIncome ? INCOME_COLOR : "#a78bfa")])), [categories]);

  return (
    <div className="sh-panel">
      <div className="sh-panel-head">
        <div className="h">{isIncome ? "Thu nhập gần đây" : "Giao dịch gần đây"}</div>
        <div className="sub">{filtered.length} giao dịch{filter !== "all" ? ` · ${filter}` : ""}</div>
      </div>
      <div style={{ maxHeight: 380, overflowY: "auto" }}>
        <table className="tx-table">
          <thead>
            <tr>
              <th style={{ width: 80 }}>Ngày</th>
              <th>Mô tả</th>
              <th style={{ width: 160 }}>Danh mục</th>
              <th style={{ width: 130, textAlign: "right" }}>Số tiền</th>
              <th style={{ width: 80, textAlign: "center" }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e, i) => (
              <tr key={i}>
                <td className="muted" style={{ fontVariantNumeric: "tabular-nums" }}>{fmtDateVN(e.date)}</td>
                <td>{e.description}</td>
                <td>
                  <span className="tx-cat-chip">
                    <span className="d" style={{ background: catMap[e.category] || (isIncome ? INCOME_COLOR : "#a78bfa") }} />
                    {e.category}
                  </span>
                </td>
                <td className={"amt " + (isIncome ? "income" : "expense")}>
                  {isIncome ? "+" : "-"}{fmtVND(e.amount).replace(/^-/, "")}
                </td>
                <td style={{ textAlign: "center" }}>
                  {e.row_number && (
                    <span style={{ display: "flex", gap: 4, justifyContent: "center" }}>
                      <button
                        className="icon-btn"
                        style={{ fontSize: 11, padding: "2px 5px" }}
                        onClick={() => onEdit(e)}
                        title="Sửa"
                      >✏️</button>
                      <button
                        className="icon-btn"
                        style={{ fontSize: 11, padding: "2px 5px", color: "var(--danger)" }}
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
                <td colSpan={5} style={{ textAlign: "center", padding: "32px", color: "var(--text-3)" }}>
                  {isIncome ? "Chưa có thu nhập nào được ghi nhận." : "Chưa có giao dịch nào trong danh mục này."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NewMonthModal({ userId, onClose, onDone }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const extractSheetId = (val) => {
    const m = val.match(/\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/);
    return m ? m[1] : val.trim();
  };

  const handle = async () => {
    const sid = extractSheetId(input);
    if (sid.length < 10) { setError("Link hoặc ID không hợp lệ."); return; }
    setLoading(true);
    setError("");
    try {
      await API.startNewMonth(userId, sid);
      onDone();
    } catch (e) {
      setError(e.message || "Có lỗi xảy ra.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "var(--ink-3)", borderRadius: 14, padding: 28, width: 460, boxShadow: "0 8px 32px rgba(0,0,0,0.35)", border: "1px solid var(--ink-5)" }}>
        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>🗓 Bắt đầu tháng mới</div>
        <p style={{ fontSize: 13, color: "var(--text-3)", marginBottom: 18, lineHeight: 1.6 }}>
          Trong Google Drive, mở sheet tháng này → <b>File → Tạo bản sao</b> → đặt tên tháng mới.<br />
          Sau đó dán link hoặc Sheet ID của bản sao đó vào đây.
        </p>
        <label style={{ fontSize: 12, color: "var(--text-3)", display: "block", marginBottom: 6 }}>Link hoặc Sheet ID của sheet tháng mới</label>
        <input
          className="input"
          style={{ width: "100%", marginBottom: 6 }}
          placeholder="https://docs.google.com/spreadsheets/d/..."
          value={input}
          onChange={e => { setInput(e.target.value); setError(""); }}
          disabled={loading}
        />
        {error && <div style={{ color: "var(--danger)", fontSize: 12, marginBottom: 8 }}>{error}</div>}
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 16 }}>
          <button className="tb-btn outline" onClick={onClose} disabled={loading}>Hủy</button>
          <button
            className="cal-create-btn"
            onClick={handle}
            disabled={loading || !input.trim()}
          >
            {loading ? "Đang xử lý..." : "Xác nhận"}
          </button>
        </div>
      </div>
    </div>
  );
}

function SheetsMain({
  activeTab, expenseItems, incomeItems, categories, incomeCategories, incomeBudgets,
  filter, onAddExpense, onAddIncome, addOpen, setAddOpen, summary,
  onEdit, onDeleteExpense, onDeleteIncome, onEditBalance, onEditBudget, onManageCategories, sheetUrl, onNewMonth
}) {
  const totalExpense = useMemo(() => expenseItems.reduce((s, e) => s + e.amount, 0), [expenseItems]);
  const totalPlanned = useMemo(() => categories.reduce((s, c) => s + c.planned, 0), [categories]);

  const isIncome = activeTab === "thu";
  const incomeCatObjs = incomeCategories.map(n => ({ name: n, color: INCOME_COLOR }));

  return (
    <div className="module-main">
      <div className="sh-toolbar">
        <div className="sh-title" style={{ color: isIncome ? "var(--success)" : undefined }}>
          {isIncome ? "↗ Thu nhập" : "↘ Chi tiêu"}
        </div>
        <div className="sh-month-pill">
          <I.Calendar2 />
          Tháng {new Date().getMonth() + 1} / {new Date().getFullYear()}
        </div>
        <div style={{ flex: 1 }} />
        <button className="tb-btn outline" onClick={onManageCategories}>
          Danh mục {isIncome ? "Thu" : "Chi"}
        </button>
        <button className="tb-btn outline" onClick={onNewMonth} title="Chuyển sang sheet tháng mới">
          🗓 Tháng mới
        </button>
        <button
          className="tb-btn outline"
          onClick={() => sheetUrl && window.open(sheetUrl, "_blank", "noopener")}
          disabled={!sheetUrl}
          title={sheetUrl ? "Mở Google Sheets" : "Chưa cấu hình Sheet ID"}
        >
          <I.Globe style={{ width: 14, height: 14 }} /> Mở trên Google Sheets
        </button>
        <button
          className="cal-create-btn"
          onClick={() => setAddOpen(true)}
          style={isIncome ? { background: "linear-gradient(135deg, #4ade80, #16a34a)" } : undefined}
        >
          <I.Plus2 /> {isIncome ? "Thêm thu nhập" : "Thêm chi tiêu"}
        </button>
      </div>

      <div className="sh-content">
        {isIncome ? (
          <>
            <IncomeSummaryCards incomeBudgets={incomeBudgets} openingBalance={summary.opening_balance} />
            {addOpen && (
              <AddTransactionForm
                isIncome={true}
                categories={incomeCatObjs.length > 0 ? incomeCatObjs : [{ name: "Thu nhập khác", color: INCOME_COLOR }]}
                onAdd={onAddIncome}
                onClose={() => setAddOpen(false)}
              />
            )}
            <IncomeCategoryBreakdown incomeBudgets={incomeBudgets} onEditBudget={onEditBudget} />
            <TransactionsTable
              expenses={incomeItems}
              categories={incomeCatObjs}
              filter={filter}
              isIncome={true}
              onEdit={(item) => onEdit(item, true)}
              onDelete={onDeleteIncome}
            />
          </>
        ) : (
          <>
            <SummaryCards
              totalActual={totalExpense}
              totalPlanned={totalPlanned}
              income={summary.total_income}
              openingBalance={summary.opening_balance}
              onEditBalance={onEditBalance}
            />
            {addOpen && (
              <AddTransactionForm
                isIncome={false}
                categories={categories}
                onAdd={onAddExpense}
                onClose={() => setAddOpen(false)}
              />
            )}
            <div className="sh-row">
              <CategoryBreakdown categories={categories} expenses={expenseItems} onEditBudget={onEditBudget} />
              <DonutBudget totalActual={totalExpense} totalPlanned={totalPlanned} />
            </div>
            <TransactionsTable
              expenses={expenseItems}
              categories={categories}
              filter={filter}
              isIncome={false}
              onEdit={(item) => onEdit(item, false)}
              onDelete={onDeleteExpense}
            />
          </>
        )}
      </div>
    </div>
  );
}

export function SheetsModule({ userId }) {
  const [activeTab, setActiveTab] = useState("chi");
  const [expenses, setExpenses] = useState([]);
  const [incomeItems, setIncomeItems] = useState([]);
  const [categories, setCategories] = useState(EXPENSE_CATEGORIES);
  const [incomeCategories, setIncomeCategories] = useState([]);
  const [incomeBudgets, setIncomeBudgets] = useState([]);
  const [filter, setFilter] = useState("all");
  const [addOpen, setAddOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({
    opening_balance: 0, closing_balance: 0, total_expenses: 0, total_income: 0,
  });
  const [editingItem, setEditingItem] = useState(null);
  const [editingIsIncome, setEditingIsIncome] = useState(false);
  const [showBalanceModal, setShowBalanceModal] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [showCategories, setShowCategories] = useState(false);
  const [sheetUrl, setSheetUrl] = useState(null);
  const [showNewMonth, setShowNewMonth] = useState(false);

  const isIncome = activeTab === "thu";

  const loadData = () => {
    if (!userId) return;
    setLoading(true);
    Promise.all([
      API.getExpenses(userId, 100),
      API.getIncomeTransactions(userId, 100),
      API.getCategories(userId),
      API.getIncomeCategories(userId),
      API.getSummary(userId),
      API.getBudgets(userId).catch(() => null),
    ])
      .then(([expData, incData, catData, incomeCatData, summaryData, budgetData]) => {
        setExpenses(Array.isArray(expData) ? expData : []);
        setIncomeItems(Array.isArray(incData) ? incData : []);

        const names = catData.categories || [];
        if (names.length > 0) {
          // Build planned lookup from sheet (live), fallback to hardcoded colors/amounts
          const apiPlanned = {};
          if (budgetData?.expense) {
            budgetData.expense.forEach(b => { apiPlanned[b.name] = b.planned; });
          }
          const merged = names.map(name => {
            const local = EXPENSE_CATEGORIES.find(c => c.name === name);
            const planned = name in apiPlanned ? apiPlanned[name] : (local?.planned ?? 0);
            return { name, color: local?.color ?? "#9ca3af", planned };
          });
          setCategories(merged);
        }

        setIncomeCategories(incomeCatData.categories || []);

        if (budgetData?.income) {
          setIncomeBudgets(budgetData.income);
        }

        if (summaryData) {
          setSummary(summaryData);
          if (summaryData.sheet_url) setSheetUrl(summaryData.sheet_url);
        }
      })
      .catch(err => console.error("Failed to load sheets data:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, [userId]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setFilter("all");
    setAddOpen(false);
  };

  const handleAddExpense = async (item) => {
    try {
      const result = await API.addExpense(userId, item);
      setExpenses(prev => [result.data, ...prev]);
    } catch (err) {
      alert("Không thể lưu: " + err.message);
    }
  };

  const handleAddIncome = async (item) => {
    try {
      const result = await API.addIncome(userId, item);
      setIncomeItems(prev => [result.data, ...prev]);
    } catch (err) {
      alert("Không thể lưu: " + err.message);
    }
  };

  const handleStartEdit = (item, isInc) => {
    setEditingItem(item);
    setEditingIsIncome(isInc);
  };

  const handleSaveEdit = async (rowNumber, data) => {
    try {
      if (editingIsIncome) {
        const updated = await API.updateIncome(userId, rowNumber, data);
        setIncomeItems(prev => prev.map(e => e.row_number === rowNumber ? { ...updated, row_number: rowNumber } : e));
      } else {
        const updated = await API.updateExpense(userId, rowNumber, data);
        setExpenses(prev => prev.map(e => e.row_number === rowNumber ? { ...updated, row_number: rowNumber } : e));
      }
      setEditingItem(null);
    } catch (err) {
      alert("Không thể cập nhật: " + err.message);
    }
  };

  const handleDeleteExpense = async (expense) => {
    if (!confirm(`Xóa chi tiêu "${expense.description}" (${fmtVND(expense.amount)})?`)) return;
    try {
      await API.deleteExpense(userId, expense.row_number);
      setExpenses(prev => prev.filter(e => e.row_number !== expense.row_number));
    } catch (err) {
      alert("Không thể xóa: " + err.message);
    }
  };

  const handleDeleteIncome = async (income) => {
    if (!confirm(`Xóa thu nhập "${income.description}" (${fmtVND(income.amount)})?`)) return;
    try {
      await API.deleteIncome(userId, income.row_number);
      setIncomeItems(prev => prev.filter(e => e.row_number !== income.row_number));
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
      if (data.is_income) {
        setIncomeBudgets(prev => prev.map(b =>
          b.name === data.category ? { ...b, planned: data.budget_amount } : b
        ));
      } else {
        setCategories(prev => prev.map(c =>
          c.name === data.category ? { ...c, planned: data.budget_amount } : c
        ));
      }
      setEditingBudget(null);
    } catch (err) {
      alert("Không thể cập nhật ngân sách: " + err.message);
    }
  };

  const editCategories = editingIsIncome
    ? incomeCategories.map(n => ({ name: n, color: INCOME_COLOR }))
    : categories;

  return (
    <>
      <SheetsSidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        activeFilter={filter}
        onFilter={setFilter}
        categories={categories}
        incomeCategories={incomeCategories}
        expenseItems={expenses}
        incomeItems={incomeItems}
        onAddOpen={() => setAddOpen(true)}
      />
      <SheetsMain
        activeTab={activeTab}
        expenseItems={expenses}
        incomeItems={incomeItems}
        categories={categories}
        incomeCategories={incomeCategories}
        incomeBudgets={incomeBudgets}
        filter={filter}
        onAddExpense={handleAddExpense}
        onAddIncome={handleAddIncome}
        addOpen={addOpen}
        setAddOpen={setAddOpen}
        summary={summary}
        onEdit={handleStartEdit}
        onDeleteExpense={handleDeleteExpense}
        onDeleteIncome={handleDeleteIncome}
        onEditBalance={() => setShowBalanceModal(true)}
        onEditBudget={setEditingBudget}
        onManageCategories={() => setShowCategories(true)}
        sheetUrl={sheetUrl}
        onNewMonth={() => setShowNewMonth(true)}
      />

      {editingItem && (
        <EditExpenseModal
          expense={editingItem}
          categories={editCategories}
          isIncome={editingIsIncome}
          onSave={handleSaveEdit}
          onClose={() => setEditingItem(null)}
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
          isIncome={isIncome}
          onSave={handleSaveBudget}
          onClose={() => setEditingBudget(null)}
        />
      )}

      {showNewMonth && (
        <NewMonthModal
          userId={userId}
          onClose={() => setShowNewMonth(false)}
          onDone={() => { setShowNewMonth(false); loadData(); }}
        />
      )}

      {showCategories && (
        <ManageCategoriesModal
          categories={isIncome
            ? incomeCategories.map(n => ({ name: n, color: INCOME_COLOR }))
            : categories
          }
          userId={userId}
          isIncome={isIncome}
          onClose={() => setShowCategories(false)}
          onRefresh={loadData}
        />
      )}
    </>
  );
}
