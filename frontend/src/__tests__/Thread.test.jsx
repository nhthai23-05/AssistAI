import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Thread } from '../components/Thread';

describe('Thread — rendering', () => {
  it('renders nothing visible when messages array is empty', () => {
    const { container } = render(
      <Thread messages={[]} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelectorAll('.msg-row')).toHaveLength(0);
  });

  it('renders one message row per message', () => {
    const messages = [
      { role: 'user', text: 'Xin chào' },
      { role: 'assistant', text: 'Chào bạn!' },
    ];
    const { container } = render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelectorAll('.msg-row')).toHaveLength(2);
  });

  it('renders message text content', () => {
    const messages = [{ role: 'user', text: 'Hôm nay thời tiết thế nào?' }];
    render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(screen.getByText('Hôm nay thời tiết thế nào?')).toBeInTheDocument();
  });
});

describe('Thread — message roles', () => {
  it('user message row has class "user"', () => {
    const messages = [{ role: 'user', text: 'Hello' }];
    const { container } = render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelector('.msg-row.user')).toBeInTheDocument();
  });

  it('assistant message row has class "ai"', () => {
    const messages = [{ role: 'assistant', text: 'Xin chào!' }];
    const { container } = render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelector('.msg-row.ai')).toBeInTheDocument();
  });

  it('user bubble has class "user", assistant bubble has class "ai"', () => {
    const messages = [
      { role: 'user', text: 'Câu hỏi' },
      { role: 'assistant', text: 'Trả lời' },
    ];
    const { container } = render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelector('.bubble.user')).toBeInTheDocument();
    expect(container.querySelector('.bubble.ai')).toBeInTheDocument();
  });
});

describe('Thread — typing indicator', () => {
  it('shows typing indicator when isTyping is true', () => {
    const { container } = render(
      <Thread messages={[]} isTyping={true} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelector('.bubble.ai.typing')).toBeInTheDocument();
  });

  it('does not show typing indicator when isTyping is false', () => {
    const { container } = render(
      <Thread messages={[]} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(container.querySelector('.bubble.typing')).not.toBeInTheDocument();
  });
});

describe('Thread — actions', () => {
  it('renders ActionCard when message has actions', () => {
    const messages = [{
      role: 'assistant',
      text: 'Tôi sẽ tạo sự kiện cho bạn.',
      actions: [{
        type: 'create_event',
        status: 'pending',
        data: { summary: 'Họp', start_datetime: '2026-06-27T09:00:00+07:00', end_datetime: '2026-06-27T10:00:00+07:00' },
      }],
    }];
    render(
      <Thread messages={messages} isTyping={false} onActionAccept={vi.fn()} onActionReject={vi.fn()} />
    );
    expect(screen.getByText('Tạo sự kiện mới')).toBeInTheDocument();
  });
});
