import { ApiConfig, StreamCallback, DoneCallback } from '@/types';

interface DashScopeMessage {
  role: 'system' | 'user';
  content: string;
}

interface DashScopeRequest {
  model: string;
  max_tokens: number;
  stream: boolean;
  messages: DashScopeMessage[];
}

function buildErrorMessage(status: number, body: string): string {
  let msg = `❌ API错误 (${status})：\n`;
  if (status === 401) msg += 'API Key 无效或已过期。';
  else if (status === 403) msg += '访问被拒绝，权限不足或跨域拦截。';
  else if (status === 429) msg += '请求超限或余额不足，请稍后重试。';
  else if (status === 400) msg += '请求格式错误或模型不支持。';
  else msg += body.slice(0, 300);
  return msg;
}

export function sendToDashScope(
  config: Pick<ApiConfig, 'apiKey' | 'model' | 'maxTokens'>,
  systemPrompt: string,
  userContent: string,
  onChunk: StreamCallback,
  onDone: DoneCallback,
): void {
  const { apiKey, model, maxTokens } = config;

  const body: DashScopeRequest = {
    model,
    max_tokens: maxTokens,
    stream: true,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userContent },
    ],
  };

  fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  })
    .then((res) => {
      if (!res.ok) {
        res.text().then((text) => {
          onChunk('\n\n' + buildErrorMessage(res.status, text));
          onDone();
        });
        return;
      }

      if (!res.body) {
        onChunk('\n\n❌ 错误：浏览器不支持流式响应。');
        onDone();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) { onDone(); return; }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (line.trim() === '') continue;
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (dataStr.trim() === '[DONE]') continue;
              try {
                const data = JSON.parse(dataStr);
                if (data.choices?.[0]?.delta?.content) {
                  onChunk(data.choices[0].delta.content as string);
                }
              } catch {
                console.warn('[DashScope] 解析流数据片段失败:', dataStr);
              }
            }
          }
          read();
        });
      }
      read();
    })
    .catch((err) => {
      onChunk(`\n\n❌ 网络错误，请检查网络或 API Key 是否有效。\n错误详情：${err.message}`);
      onDone();
    });
}
