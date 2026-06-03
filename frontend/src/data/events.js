const _now = new Date();

const _startOfWeek = (d) => {
  const x = new Date(d);
  const dow = (x.getDay() + 6) % 7;
  x.setDate(x.getDate() - dow);
  x.setHours(0, 0, 0, 0);
  return x;
};

const _addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const _atTime = (d, h, m = 0) => { const x = new Date(d); x.setHours(h, m, 0, 0); return x.getTime(); };

const weekStart = _startOfWeek(_now);

export const EVENTS = [
  // Monday
  { id: "ev1",  color: "violet",  summary: "Stand-up nhóm",               start: _atTime(_addDays(weekStart,0), 9,  0), end: _atTime(_addDays(weekStart,0), 9, 30), location: "Google Meet",                      attendees: ["thai@assistai.dev","linh@assistai.dev","minh@assistai.dev"], description: "Daily sync — review sprint goals" },
  { id: "ev2",  color: "cyan",    summary: "Phỏng vấn ứng viên Backend",  start: _atTime(_addDays(weekStart,0), 14, 0), end: _atTime(_addDays(weekStart,0), 15, 0), location: "Văn phòng — phòng họp B",           attendees: ["hr@assistai.dev"],                                            description: "Technical round — FastAPI + Postgres" },
  // Tuesday
  { id: "ev3",  color: "violet",  summary: "Stand-up nhóm",               start: _atTime(_addDays(weekStart,1), 9,  0), end: _atTime(_addDays(weekStart,1), 9, 30), location: "Google Meet" },
  { id: "ev4",  color: "pink",    summary: "Họp với khách hàng VPBank",   start: _atTime(_addDays(weekStart,1), 10, 30), end: _atTime(_addDays(weekStart,1), 12, 0), location: "VPBank Tower, Hà Nội",             attendees: ["khanh.tran@vpbank.com.vn","linh@assistai.dev"],               description: "Demo bản POC tích hợp Calendar/Sheets" },
  { id: "ev5",  color: "amber",   summary: "Gym buổi chiều",              start: _atTime(_addDays(weekStart,1), 18, 30), end: _atTime(_addDays(weekStart,1), 20, 0), location: "California Fitness — Vincom" },
  // Wednesday
  { id: "ev6",  color: "violet",  summary: "Stand-up nhóm",               start: _atTime(_addDays(weekStart,2), 9,  0), end: _atTime(_addDays(weekStart,2), 9, 30) },
  { id: "ev7",  color: "emerald", summary: "Code review — PR #142",       start: _atTime(_addDays(weekStart,2), 11, 0), end: _atTime(_addDays(weekStart,2), 11, 45),                                                                                                                                    description: "OAuth refresh token flow + encrypted storage" },
  { id: "ev8",  color: "cyan",    summary: "1:1 với Linh",                start: _atTime(_addDays(weekStart,2), 14, 0), end: _atTime(_addDays(weekStart,2), 14, 30), location: "Google Meet" },
  { id: "ev9",  color: "pink",    summary: "Coffee chat — Mai (UI/UX)",   start: _atTime(_addDays(weekStart,2), 16, 0), end: _atTime(_addDays(weekStart,2), 17, 0), location: "The Coffee House — Lý Thường Kiệt" },
  // Thursday
  { id: "ev10", color: "violet",  summary: "Stand-up nhóm",               start: _atTime(_addDays(weekStart,3), 9,  0), end: _atTime(_addDays(weekStart,3), 9, 30) },
  { id: "ev11", color: "amber",   summary: "Sprint planning",             start: _atTime(_addDays(weekStart,3), 13, 30), end: _atTime(_addDays(weekStart,3), 15, 30), attendees: ["thai@assistai.dev","linh@assistai.dev","minh@assistai.dev","hao@assistai.dev"], description: "Plan sprint 14 — frontend integration" },
  // Friday
  { id: "ev12", color: "violet",  summary: "Stand-up nhóm",               start: _atTime(_addDays(weekStart,4), 9,  0), end: _atTime(_addDays(weekStart,4), 9, 30) },
  { id: "ev13", color: "emerald", summary: "Demo nội bộ — AI Assistant",  start: _atTime(_addDays(weekStart,4), 15, 0), end: _atTime(_addDays(weekStart,4), 16, 0), location: "Văn phòng — phòng họp lớn",         description: "Show calendar & sheets module end-to-end" },
  { id: "ev14", color: "pink",    summary: "Tối với Phương",              start: _atTime(_addDays(weekStart,4), 19, 0), end: _atTime(_addDays(weekStart,4), 21, 0), location: "Pizza 4P's — Phan Kế Bính" },
  // Saturday
  { id: "ev15", color: "amber",   summary: "Chạy bộ hồ Tây",             start: _atTime(_addDays(weekStart,5), 6, 30), end: _atTime(_addDays(weekStart,5), 7, 30) },
  { id: "ev16", color: "cyan",    summary: "Workshop AI ở UET",           start: _atTime(_addDays(weekStart,5), 14, 0), end: _atTime(_addDays(weekStart,5), 17, 0), location: "Trường ĐH Công nghệ — ĐHQGHN",       description: "Chia sẻ về FastAPI + OpenAI tools" },
];
