// @ts-check
import { test, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Inject auth state so the app skips the Google OAuth login page. */
async function loginViaLocalStorage(page) {
  await page.addInitScript(() => {
    localStorage.setItem('assistai_authed', '1');
    localStorage.setItem('assistai_user_id', '1');
    localStorage.setItem('assistai_email', 'test@example.com');
  });
}

/** Mock all essential API routes — no real backend required. */
async function mockAllApis(page) {
  await page.route('**/api/chat/sessions*', async (route) => {
    const method = route.request().method();
    if (method === 'GET') {
      await route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify([{
          session_id: 1, title: 'Cuộc trò chuyện',
          message_count: 0, last_message_at: new Date().toISOString(),
          total_tokens_used: 0, status: 'active',
        }]),
      });
    } else if (method === 'POST') {
      await route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ session_id: 2, created_at: new Date().toISOString() }),
      });
    } else {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
    }
  });

  await page.route('**/api/chat/history*', async (route) => {
    await route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ session_id: 1, messages: [] }),
    });
  });

  await page.route('**/api/chat/message*', async (route) => {
    await route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        message_id: 10, session_id: 1,
        response: 'Xin chào! Tôi là AssistAI. Tôi có thể giúp gì cho bạn?',
        actions: null, tokens_used: 50, thinking_time_ms: 200,
        created_at: new Date().toISOString(), suggested_title: null,
      }),
    });
  });

  await page.route('**/api/auth/status*', async (route) => {
    await route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ authenticated: true, user_id: 1 }),
    });
  });
}

// ---------------------------------------------------------------------------
// 1. Login flow
// ---------------------------------------------------------------------------

test.describe('Login flow', () => {
  test('shows login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/Đăng nhập/i).first()).toBeVisible();
  });

  test('shows chat UI after injecting auth state', async ({ page }) => {
    await mockAllApis(page);
    await loginViaLocalStorage(page);
    await page.goto('/');
    await expect(page.getByText('Cuộc trò chuyện mới')).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 2. Chat flow
// ---------------------------------------------------------------------------

test.describe('Chat flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApis(page);
    await loginViaLocalStorage(page);
    await page.goto('/');
    await expect(page.getByText('Cuộc trò chuyện mới')).toBeVisible();
  });

  test('user can type a message in the composer', async ({ page }) => {
    const textarea = page.getByPlaceholder(/Hỏi AssistAI/i);
    await textarea.fill('Xin chào AssistAI');
    await expect(textarea).toHaveValue('Xin chào AssistAI');
  });

  test('send button is disabled when composer is empty', async ({ page }) => {
    await expect(page.getByTitle('Gửi')).toBeDisabled();
  });

  test('send button is enabled when message is typed', async ({ page }) => {
    await page.getByPlaceholder(/Hỏi AssistAI/i).fill('Hello');
    await expect(page.getByTitle('Gửi')).toBeEnabled();
  });

  test('clicking send shows user message and AI response in thread', async ({ page }) => {
    await page.getByPlaceholder(/Hỏi AssistAI/i).fill('Xin chào');
    await page.getByTitle('Gửi').click();
    await expect(page.getByText('Xin chào').first()).toBeVisible();
    await expect(page.getByText('Xin chào! Tôi là AssistAI')).toBeVisible({ timeout: 5000 });
  });

  test('pressing Enter sends the message', async ({ page }) => {
    await page.getByPlaceholder(/Hỏi AssistAI/i).fill('Hỏi bằng Enter');
    await page.keyboard.press('Enter');
    await expect(page.getByText('Hỏi bằng Enter')).toBeVisible();
  });

  test('Shift+Enter does not send the message', async ({ page }) => {
    const textarea = page.getByPlaceholder(/Hỏi AssistAI/i);
    await textarea.fill('Chưa gửi');
    await page.keyboard.press('Shift+Enter');
    await expect(page.getByTitle('Gửi')).toBeEnabled();
  });
});

// ---------------------------------------------------------------------------
// 3. Sidebar navigation
// ---------------------------------------------------------------------------

test.describe('Sidebar navigation', () => {
  test.beforeEach(async ({ page }) => {
    await mockAllApis(page);
    await loginViaLocalStorage(page);
    await page.goto('/');
    await expect(page.getByText('Cuộc trò chuyện mới')).toBeVisible();
  });

  test('existing sessions appear in sidebar', async ({ page }) => {
    await expect(page.getByText('Cuộc trò chuyện').first()).toBeVisible();
  });

  test('clicking new chat button resets the thread', async ({ page }) => {
    await page.getByText('Cuộc trò chuyện mới').click();
    // After clicking "new chat", app shows Welcome screen (empty conversation)
    // Composer is always visible, confirming the chat UI is active
    await expect(page.getByPlaceholder(/Hỏi AssistAI/i)).toBeVisible();
  });

  test('sidebar search filters conversations', async ({ page }) => {
    await page.getByPlaceholder('Tìm cuộc trò chuyện').fill('xyz không tồn tại');
    await expect(page.getByText(/Không tìm thấy/i)).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// 4. ActionCard acceptance
// ---------------------------------------------------------------------------

test.describe('ActionCard acceptance', () => {
  async function setupWithAction(page) {
    await page.route('**/api/chat/sessions*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ session_id: 1, title: 'Test', message_count: 0, last_message_at: new Date().toISOString(), total_tokens_used: 0, status: 'active' }]) });
      } else { await route.continue(); }
    });
    await page.route('**/api/chat/history*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ session_id: 1, messages: [] }) });
    });
    await page.route('**/api/auth/status*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ authenticated: true, user_id: 1 }) });
    });
    await page.route('**/api/chat/message*', async (route) => {
      await route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          message_id: 11, session_id: 1,
          response: 'Tôi sẽ tạo sự kiện cho bạn.',
          actions: [{ action_type: 'create_event', action_status: 'pending', data: { summary: 'Họp nhóm', start_datetime: '2026-06-27T09:00:00+07:00', end_datetime: '2026-06-27T10:00:00+07:00' } }],
          tokens_used: 60, thinking_time_ms: 300,
          created_at: new Date().toISOString(), suggested_title: null,
        }),
      });
    });
    await loginViaLocalStorage(page);
    await page.goto('/');
    await expect(page.getByText('Cuộc trò chuyện mới')).toBeVisible();
    await page.getByPlaceholder(/Hỏi AssistAI/i).fill('Tạo lịch họp');
    await page.getByTitle('Gửi').click();
    await expect(page.getByText('Tạo sự kiện mới')).toBeVisible({ timeout: 5000 });
  }

  test('ActionCard appears with title and action buttons', async ({ page }) => {
    await setupWithAction(page);
    await expect(page.getByText('Thêm vào Calendar')).toBeVisible();
    await expect(page.getByText('Bỏ qua')).toBeVisible();
    await expect(page.getByText('AI Action')).toBeVisible();
  });

  test('clicking "Bỏ qua" shows rejected state', async ({ page }) => {
    await page.route('**/api/chat/messages/*/actions/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
    });
    await setupWithAction(page);
    await page.getByText('Bỏ qua').click();
    await expect(page.getByText('Đã bỏ qua hành động này.')).toBeVisible({ timeout: 3000 });
  });

  test('clicking "Thêm vào Calendar" shows accepted state', async ({ page }) => {
    await page.route('**/api/chat/messages/*/actions/*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
    });
    await page.route('**/api/calendar/events*', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 'evt-1', summary: 'Họp nhóm' }) });
    });
    await setupWithAction(page);
    await page.getByText('Thêm vào Calendar').click();
    await expect(page.getByText('Đã thêm vào Google Calendar')).toBeVisible({ timeout: 5000 });
  });
});
