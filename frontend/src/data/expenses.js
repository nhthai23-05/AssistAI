export const EXPENSE_CATEGORIES = [
  { name: "Ăn uống",           color: "#f472b6", planned: 600000 },
  { name: "Quà tặng",          color: "#fbbf24", planned: 300000 },
  { name: "Sức khỏe/y tế",     color: "#34d399", planned: 500000 },
  { name: "Nhà",               color: "#a78bfa", planned: 500000 },
  { name: "Nghe gọi",          color: "#60a5fa", planned: 100000 },
  { name: "Cá nhân",           color: "#f87171", planned: 500000 },
  { name: "Đầu tư",            color: "#22d3ee", planned: 300000 },
  // { name: "Phương yêu",        color: "#fb7185", planned: 500000 },
  { name: "Đi lại",            color: "#fb923c", planned: 400000 },
  { name: "Nợ",                color: "#94a3b8", planned: 2500000 },
  { name: "Vui chơi giải trí", color: "#c084fc", planned: 1000000 },
  { name: "Công việc",         color: "#67e8f9", planned: 0 },
  { name: "Giáo dục",          color: "#86efac", planned: 0 },
  { name: "Khác",              color: "#9ca3af", planned: 200000 },
];

const _thisMonth = (day) => {
  const d = new Date();
  d.setDate(day);
  d.setHours(0, 0, 0, 0);
  return d.toISOString().slice(0, 10);
};

export const EXPENSES = [
  { date: _thisMonth(1),  amount: 250000,  description: "Cơm trưa cả tuần",                        category: "Ăn uống" },
  { date: _thisMonth(2),  amount: 100000,  description: "Thẻ nạp Viettel",                          category: "Nghe gọi" },
  { date: _thisMonth(3),  amount: 480000,  description: "Mua sách Designing Data-Intensive Apps",   category: "Giáo dục" },
  { date: _thisMonth(4),  amount: 110000,  description: "Mua cổ phiếu lẻ — VND",                   category: "Đầu tư" },
  { date: _thisMonth(5),  amount: 89000,   description: "Phở Thìn",                                 category: "Ăn uống" },
  { date: _thisMonth(6),  amount: 240000,  description: "Grab — đi lại tuần",                       category: "Đi lại" },
  { date: _thisMonth(7),  amount: 350000,  description: "Áo polo Coolmate",                         category: "Cá nhân" },
  { date: _thisMonth(8),  amount: 165000,  description: "Cinema — Inside Out 2",                    category: "Vui chơi giải trí" },
  // { date: _thisMonth(9),  amount: 215000,  description: "Bữa tối với Phương — Manwah",              category: "Phương yêu" },
  { date: _thisMonth(10), amount: 78000,   description: "Bún bò Huế",                               category: "Ăn uống" },
  { date: _thisMonth(11), amount: 1200000, description: "Concert Hà Anh Tuấn — vé đôi",            category: "Vui chơi giải trí" },
  // { date: _thisMonth(12), amount: 450000,  description: "Hoa & quà sinh nhật Phương",               category: "Phương yêu" },
  { date: _thisMonth(13), amount: 710000,  description: "Tài khoản OpenAI API tháng",               category: "Công việc" },
  { date: _thisMonth(14), amount: 137000,  description: "Highlands Coffee × 4",                     category: "Ăn uống" },
  { date: _thisMonth(15), amount: 229000,  description: "Tai nghe có dây — backup",                 category: "Cá nhân" },
  { date: _thisMonth(16), amount: 858343,  description: "Apple Music + iCloud + Spotify (cả năm)", category: "Cá nhân" },
];

export const fmtVND = (n) => {
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(Math.round(n));
  return sign + abs.toLocaleString("vi-VN") + " ₫";
};

export const fmtDateVN = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
};

export const fmtTimeVN = (ts) => {
  const d = new Date(ts);
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", hour12: false });
};
