import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Composer } from '../components/Composer';

function renderComposer(overrides = {}) {
  const defaults = {
    value: '',
    onChange: vi.fn(),
    onSend: vi.fn(),
    onStop: vi.fn(),
    isTyping: false,
    modelLabel: 'GPT-4o',
    image: null,
    onImageChange: vi.fn(),
  };
  return render(<Composer {...defaults} {...overrides} />);
}

describe('Composer — rendering', () => {
  it('renders the textarea with placeholder', () => {
    renderComposer();
    expect(screen.getByPlaceholderText(/Hỏi AssistAI/i)).toBeInTheDocument();
  });

  it('renders the send button (title="Gửi")', () => {
    renderComposer();
    expect(screen.getByTitle('Gửi')).toBeInTheDocument();
  });

  it('displays the model label', () => {
    renderComposer({ modelLabel: 'GPT-4o' });
    expect(screen.getByText('GPT-4o')).toBeInTheDocument();
  });
});

describe('Composer — send button state', () => {
  it('send button is disabled when value is empty', () => {
    renderComposer({ value: '' });
    expect(screen.getByTitle('Gửi')).toBeDisabled();
  });

  it('send button is disabled when value is only whitespace', () => {
    renderComposer({ value: '   ' });
    expect(screen.getByTitle('Gửi')).toBeDisabled();
  });

  it('send button is enabled when value has text', () => {
    renderComposer({ value: 'Xin chào' });
    expect(screen.getByTitle('Gửi')).not.toBeDisabled();
  });

  it('send button is enabled when image is present even without text', () => {
    renderComposer({ value: '', image: 'data:image/png;base64,abc' });
    expect(screen.getByTitle('Gửi')).not.toBeDisabled();
  });

  it('stop button shown instead of send when isTyping', () => {
    renderComposer({ value: 'hello', isTyping: true });
    expect(screen.queryByTitle('Gửi')).not.toBeInTheDocument();
    expect(screen.getByTitle('Dừng')).toBeInTheDocument();
  });
});

describe('Composer — interactions', () => {
  it('calls onSend when send button is clicked with non-empty value', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderComposer({ value: 'Hello', onSend });
    await user.click(screen.getByTitle('Gửi'));
    expect(onSend).toHaveBeenCalledOnce();
  });

  it('does not call onSend when send button is disabled (empty value)', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderComposer({ value: '', onSend });
    // disabled button ignores click
    const btn = screen.getByTitle('Gửi');
    expect(btn).toBeDisabled();
    expect(onSend).not.toHaveBeenCalled();
  });

  it('calls onChange when user types in textarea', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderComposer({ onChange });
    await user.type(screen.getByPlaceholderText(/Hỏi AssistAI/i), 'a');
    expect(onChange).toHaveBeenCalled();
  });

  it('Enter key calls onSend when value is non-empty', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderComposer({ value: 'Xin chào', onSend });
    await user.type(screen.getByPlaceholderText(/Hỏi AssistAI/i), '{Enter}');
    expect(onSend).toHaveBeenCalledOnce();
  });

  it('Shift+Enter does not call onSend', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderComposer({ value: 'Xin chào', onSend });
    await user.type(screen.getByPlaceholderText(/Hỏi AssistAI/i), '{Shift>}{Enter}{/Shift}');
    expect(onSend).not.toHaveBeenCalled();
  });

  it('calls onStop when stop button is clicked during typing', async () => {
    const user = userEvent.setup();
    const onStop = vi.fn();
    renderComposer({ value: '', isTyping: true, onStop });
    await user.click(screen.getByTitle('Dừng'));
    expect(onStop).toHaveBeenCalledOnce();
  });
});
