import React from 'react';
import I from './icons';

const SUGGESTIONS = [
  { icon: <I.Calendar2/>, title: "Tạo sự kiện mới",      desc: "VD: \"Đặt lịch họp với team vào 3h chiều mai\"" },
  { icon: <I.Wallet/>,    title: "Ghi giao dịch nhanh",   desc: "VD: \"Hôm nay ăn trưa hết 85k, danh mục ăn uống\"" },
  { icon: <I.Map/>,       title: "Hỏi về lịch tuần này",  desc: "VD: \"Tuần này tôi có buổi họp nào?\"" },
  { icon: <I.Flask/>,     title: "Phân tích chi tiêu",    desc: "VD: \"Tôi đã chi bao nhiêu cho ăn uống tháng này?\"" },
];

export function Welcome({ onPick }) {
  return (
    <div className="welcome">
      <div className="welcome-mark">
        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#fff" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round">
          <path d="m12 3 4 5-4 13-4-13 4-5Z" fill="rgba(255,255,255,.2)"/>
        </svg>
      </div>
      <h1>Xin chào! Tôi có thể giúp gì cho bạn?</h1>
      <p>Hỏi tôi bất cứ điều gì về lịch, thu chi, hoặc các tác vụ hàng ngày. Chọn một gợi ý dưới đây để bắt đầu.</p>
      <div className="suggestions">
        {SUGGESTIONS.map((s, i) => (
          <button key={i} className="suggest" onClick={() => onPick(s.title)}>
            <div className="s-icon">{s.icon}</div>
            <div className="s-title">{s.title}</div>
            <div className="s-desc">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
