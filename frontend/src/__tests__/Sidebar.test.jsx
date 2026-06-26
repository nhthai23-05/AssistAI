import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Sidebar } from '../components/Sidebar';

const today = new Date();

const sampleConversations = [
  { id: 1, title: 'Lập kế hoạch tuần', updatedAt: today, pinned: false },
  { id: 2, title: 'Ghi chi phí tháng 6', updatedAt: today, pinned: false },
  { id: 3, title: 'Sự kiện được ghim', updatedAt: today, pinned: true },
];

function renderSidebar(overrides = {}) {
  const defaults = {
    conversations: sampleConversations,
    activeId: null,
    onSelect: vi.fn(),
    onNew: vi.fn(),
    onDelete: vi.fn(),
    userEmail: 'user@example.com',
  };
  return render(<Sidebar {...defaults} {...overrides} />);
}

describe('Sidebar — rendering', () => {
  it('renders brand name "AssistAI"', () => {
    renderSidebar();
    expect(screen.getByText('AssistAI')).toBeInTheDocument();
  });

  it('renders all conversation titles', () => {
    renderSidebar();
    expect(screen.getByText('Lập kế hoạch tuần')).toBeInTheDocument();
    expect(screen.getByText('Ghi chi phí tháng 6')).toBeInTheDocument();
    expect(screen.getByText('Sự kiện được ghim')).toBeInTheDocument();
  });

  it('renders "Cuộc trò chuyện mới" button', () => {
    renderSidebar();
    expect(screen.getByText('Cuộc trò chuyện mới')).toBeInTheDocument();
  });

  it('renders search input', () => {
    renderSidebar();
    expect(screen.getByPlaceholderText('Tìm cuộc trò chuyện')).toBeInTheDocument();
  });

  it('shows user display name derived from email', () => {
    renderSidebar({ userEmail: 'hoangthai@gmail.com' });
    expect(screen.getByText('hoangthai')).toBeInTheDocument();
  });

  it('shows "Đã ghim" group for pinned conversations', () => {
    renderSidebar();
    expect(screen.getByText('Đã ghim')).toBeInTheDocument();
  });

  it('shows "Hôm nay" group for today conversations', () => {
    renderSidebar();
    expect(screen.getByText('Hôm nay')).toBeInTheDocument();
  });
});

describe('Sidebar — active conversation', () => {
  it('active conversation has class "active"', () => {
    const { container } = renderSidebar({ activeId: 1 });
    expect(container.querySelectorAll('.conv.active')).toHaveLength(1);
  });

  it('non-active conversations do not have class "active"', () => {
    const { container } = renderSidebar({ activeId: 1 });
    const allItems = container.querySelectorAll('.conv');
    const nonActive = [...allItems].filter(el => !el.classList.contains('active'));
    expect(nonActive.length).toBeGreaterThan(0);
  });
});

describe('Sidebar — interactions', () => {
  it('calls onSelect with conversation id when clicked', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderSidebar({ onSelect });
    await user.click(screen.getByText('Lập kế hoạch tuần'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('calls onNew when "Cuộc trò chuyện mới" is clicked', async () => {
    const user = userEvent.setup();
    const onNew = vi.fn();
    renderSidebar({ onNew });
    await user.click(screen.getByText('Cuộc trò chuyện mới'));
    expect(onNew).toHaveBeenCalledOnce();
  });

  it('calls onDelete but not onSelect when delete button is clicked', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    const onSelect = vi.fn();
    renderSidebar({ onDelete, onSelect });
    const deleteButtons = screen.getAllByTitle('Xóa cuộc trò chuyện');
    await user.click(deleteButtons[0]);
    expect(onDelete).toHaveBeenCalledOnce();
    expect(onSelect).not.toHaveBeenCalled();
  });
});

describe('Sidebar — search', () => {
  it('filters conversations by search query', async () => {
    const user = userEvent.setup();
    renderSidebar();
    await user.type(screen.getByPlaceholderText('Tìm cuộc trò chuyện'), 'chi phí');
    expect(screen.getByText('Ghi chi phí tháng 6')).toBeInTheDocument();
    expect(screen.queryByText('Lập kế hoạch tuần')).not.toBeInTheDocument();
  });

  it('shows not-found message when no conversations match', async () => {
    const user = userEvent.setup();
    renderSidebar();
    await user.type(screen.getByPlaceholderText('Tìm cuộc trò chuyện'), 'xyz không tồn tại');
    expect(screen.getByText(/Không tìm thấy/i)).toBeInTheDocument();
  });
});
