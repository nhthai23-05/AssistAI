import React, { useState } from 'react';
import I from '../components/icons';
import API from '../services/api';

export function LoginPage({ onLogin }) {
  const [loading, setLoading] = useState(false);

  const handle = () => {
    setLoading(true);
    const popup = window.open(`${API.base}/api/auth/login`, "google_oauth", "width=520,height=640,scrollbars=yes,resizable=yes");
    if (!popup) {
      setLoading(false);
      alert("Trình duyệt đã chặn popup. Vui lòng cho phép popup cho trang này và thử lại.");
      return;
    }
    const listener = (e) => {
      if (e.data?.type === "auth_success") {
        window.removeEventListener("message", listener);
        clearInterval(pollClosed);
        setLoading(false);
        onLogin(e.data.user_id, e.data.email);
      }
    };
    window.addEventListener("message", listener);
    const pollClosed = setInterval(() => {
      if (popup.closed) { clearInterval(pollClosed); window.removeEventListener("message", listener); setLoading(false); }
    }, 500);
  };

  return (
    <div className="login-root">
      <div className="login-bg-orb" style={{ width: 400, height: 400, background: "#7c3aed", left: -100, top: -100 }}/>
      <div className="login-bg-orb" style={{ width: 500, height: 500, background: "#4f46e5", right: -150, bottom: -150 }}/>
      <div className="login-card">
        <div className="login-mark"><I.Logo style={{ width: 28, height: 28, stroke: "#fff" }}/></div>
        <h1>Chào mừng đến với AssistAI</h1>
        <p className="sub">Trợ lý AI giúp bạn quản lý lịch làm việc và thu chi cá nhân — tích hợp Google Calendar &amp; Google Sheets.</p>
        <button className="google-btn" onClick={handle} disabled={loading}>
          {loading ? (<><I.Loading className="spin"/><span>Đang kết nối với Google…</span></>) : (<><I.Google/><span>Đăng nhập với Google</span></>)}
        </button>
        <div className="login-perks">
          <div className="login-perk">
            <div className="pi"><I.Calendar2/></div>
            <div><div className="pt">Lịch tự động</div><div className="pd">Tạo, sửa, xóa sự kiện chỉ bằng câu lệnh tự nhiên.</div></div>
          </div>
          <div className="login-perk">
            <div className="pi"><I.Wallet/></div>
            <div><div className="pt">Thu chi thông minh</div><div className="pd">Ghi nhanh giao dịch vào Google Sheets, phân loại tự động.</div></div>
          </div>
          <div className="login-perk">
            <div className="pi"><I.Shield/></div>
            <div><div className="pt">Bảo mật OAuth 2.0</div><div className="pd">Token mã hóa Fernet, lưu local. Không lưu mật khẩu Google của bạn.</div></div>
          </div>
        </div>
        <div className="login-foot">Khi đăng nhập, bạn đồng ý với <a href="#">Điều khoản</a> và <a href="#">Chính sách quyền riêng tư</a>.</div>
      </div>
    </div>
  );
}
