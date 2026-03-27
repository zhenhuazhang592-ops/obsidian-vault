import { useState } from 'react';
import { useStore } from '@/store';
import { Field } from '@/components/ui';

interface SettingsModalProps {
  onClose: () => void;
}

export function SettingsModal({ onClose }: SettingsModalProps) {
  const { apiConfig, setApiConfig, clearAll } = useStore();
  const [localSettings, setLocalSettings] = useState({
    apiKey: apiConfig.apiKey,
    model: apiConfig.model,
    maxTokens: String(apiConfig.maxTokens),
  });

  function save() {
    setApiConfig({
      apiKey: localSettings.apiKey,
      model: localSettings.model,
      maxTokens: parseInt(localSettings.maxTokens) || 8192,
    });
    onClose();
  }

  function handleClear() {
    if (window.confirm('确定清除本地所有已生成的内容和缓存？')) {
      clearAll();
      localStorage.clear();
      window.location.reload();
    }
  }

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-box">
        <h2 className="modal-title">⚙️ 模型接口设置</h2>
        <Field label="模型版本">
          <select
            className="field-input"
            value={localSettings.model}
            onChange={(e) => setLocalSettings((p) => ({ ...p, model: e.target.value }))}
          >
            <option value="qwen-max">通义千问 Max (推荐)</option>
            <option value="qwen-plus">通义千问 Plus</option>
            <option value="qwen-turbo">通义千问 Turbo</option>
            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
          </select>
        </Field>
        <Field label="API Key (DashScope)">
          <input
            type="password"
            className="field-input"
            value={localSettings.apiKey}
            onChange={(e) => setLocalSettings((p) => ({ ...p, apiKey: e.target.value }))}
            placeholder="sk-xxxxxxxx..."
          />
        </Field>
        <Field label="最大输出 Token">
          <input
            type="number"
            className="field-input"
            value={localSettings.maxTokens}
            onChange={(e) => setLocalSettings((p) => ({ ...p, maxTokens: e.target.value }))}
            placeholder="8192"
          />
        </Field>
        <div className="modal-actions">
          <button type="button" className="btn-danger" onClick={handleClear}>
            🗑️ 清空数据
          </button>
          <button type="button" className="btn-ghost" onClick={onClose}>
            取消
          </button>
          <button type="button" className="btn-primary" onClick={save}>
            保存应用
          </button>
        </div>
      </div>
    </div>
  );
}
