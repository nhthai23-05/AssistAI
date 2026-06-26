import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActionCard } from '../components/ActionCard';

const baseAction = {
  type: 'create_event',
  status: 'pending',
  data: { summary: 'Họp nhóm', start_datetime: '2026-06-27T09:00:00+07:00', end_datetime: '2026-06-27T10:00:00+07:00' },
};

describe('ActionCard — pending state', () => {
  it('renders "Tạo sự kiện mới" title for create_event', () => {
    render(<ActionCard action={baseAction} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Tạo sự kiện mới')).toBeInTheDocument();
  });

  it('renders "Ghi khoản chi" for write_sheet (single)', () => {
    const action = { type: 'write_sheet', status: 'pending', data: { amount: 50000, description: 'Cà phê', date: '2026-06-27' } };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Ghi khoản chi')).toBeInTheDocument();
  });

  it('renders "Ghi N khoản chi" for write_sheet with array data', () => {
    const action = {
      type: 'write_sheet', status: 'pending',
      data: [{ amount: 50000, description: 'A' }, { amount: 30000, description: 'B' }],
    };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Ghi 2 khoản chi')).toBeInTheDocument();
  });

  it('shows "AI Action" badge in pending state', () => {
    render(<ActionCard action={baseAction} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('AI Action')).toBeInTheDocument();
  });

  it('calls onAccept when accept button is clicked', async () => {
    const user = userEvent.setup();
    const onAccept = vi.fn();
    render(<ActionCard action={baseAction} onAccept={onAccept} onReject={vi.fn()} />);
    await user.click(screen.getByText('Thêm vào Calendar'));
    expect(onAccept).toHaveBeenCalledOnce();
  });

  it('calls onReject when "Bỏ qua" button is clicked', async () => {
    const user = userEvent.setup();
    const onReject = vi.fn();
    render(<ActionCard action={baseAction} onAccept={vi.fn()} onReject={onReject} />);
    await user.click(screen.getByText('Bỏ qua'));
    expect(onReject).toHaveBeenCalledOnce();
  });

  it('shows "Xóa" as accept label for delete_event', () => {
    const action = { type: 'delete_event', status: 'pending', data: { event_summary: 'Họp' } };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Xóa')).toBeInTheDocument();
  });
});

describe('ActionCard — accepted state', () => {
  it('shows accepted confirmation text for create_event', () => {
    const action = { ...baseAction, status: 'accepted' };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Đã thêm vào Google Calendar')).toBeInTheDocument();
  });

  it('does not show Accept/Reject buttons when accepted', () => {
    const action = { ...baseAction, status: 'accepted' };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.queryByText('Bỏ qua')).not.toBeInTheDocument();
    expect(screen.queryByText('Thêm vào Calendar')).not.toBeInTheDocument();
  });

  it('shows accepted text for write_sheet', () => {
    const action = { type: 'write_sheet', status: 'accepted', data: { amount: 50000 } };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Đã ghi khoản chi vào Google Sheets')).toBeInTheDocument();
  });
});

describe('ActionCard — rejected state', () => {
  it('shows "Đã bỏ qua hành động này." when rejected', () => {
    const action = { ...baseAction, status: 'rejected' };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('Đã bỏ qua hành động này.')).toBeInTheDocument();
  });

  it('does not show Accept/Reject buttons when rejected', () => {
    const action = { ...baseAction, status: 'rejected' };
    render(<ActionCard action={action} onAccept={vi.fn()} onReject={vi.fn()} />);
    expect(screen.queryByText('Bỏ qua')).not.toBeInTheDocument();
  });
});
