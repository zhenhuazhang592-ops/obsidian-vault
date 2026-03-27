import { useCallback } from 'react';
import { useStore } from '@/store';
import { sendToDashScope } from '@/services/dashscope';

export function useGenerate() {
  const { saveOutput, setLoading } = useStore();

  const gen = useCallback(
    (key: string, systemPrompt: string, userContent: string) => {
      const { apiKey, model, maxTokens } = useStore.getState().apiConfig;

      if (!apiKey) {
        saveOutput(key, '\n\n❌ 错误：请先在右上角设置 API Key！\n访问 https://dashscope.console.aliyun.com 获取密钥。\n');
        setLoading(key, false);
        return;
      }

      saveOutput(key, '');
      setLoading(key, true);

      sendToDashScope(
        { apiKey, model, maxTokens },
        systemPrompt,
        userContent,
        (chunk) => {
          const current = useStore.getState().outputs[key] ?? '';
          saveOutput(key, current + chunk);
        },
        () => {
          setLoading(key, false);
        },
      );
    },
    [saveOutput, setLoading],
  );

  return { gen };
}
