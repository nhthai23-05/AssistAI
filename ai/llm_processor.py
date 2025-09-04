"""
LLM_PROCESSOR.PY - Large Language Model Handler
==============================================
Mục đích: Xử lý tất cả các tương tác với LLM (OpenAI, Claude, etc.)
Chức năng:
- Initialize LLM clients (OpenAI API, Anthropic API)
- Process natural language requests
- Format responses cho user interface
- Handle API rate limiting và retries
- Manage conversation context và memory
- Cost tracking cho API calls
Dependencies: ai.prompt_manager, utils.config
"""